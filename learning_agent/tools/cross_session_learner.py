"""
Cross-Session Learning Application for LearningAgent.

Applies historical patterns and learnings from previous sessions to current operations.
"""

import json
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta

from agency_swarm.tools import BaseTool
from pydantic import Field

from shared.type_definitions.json import JSONValue


def _safe_get_str(data: JSONValue, key: str, default: str = "") -> str:
    """Safely extract string from JSONValue dict with type checking."""
    if isinstance(data, dict) and key in data:
        value = data[key]
        if isinstance(value, str):
            return value
    return default


def _safe_get_list(data: JSONValue, key: str, default: list[str] | None = None) -> list[str]:
    """Safely extract list of strings from JSONValue dict with type checking."""
    if default is None:
        default = []
    if isinstance(data, dict) and key in data:
        value = data[key]
        if isinstance(value, list):
            return [str(item) for item in value if isinstance(item, str)]
    return default


def _safe_get_float(data: JSONValue, key: str, default: float = 0.0) -> float:
    """Safely extract float from JSONValue dict with type checking."""
    if isinstance(data, dict) and key in data:
        value = data[key]
        if isinstance(value, (int, float)):
            return float(value)
    return default


def _safe_get_int(data: JSONValue, key: str, default: int = 0) -> int:
    """Safely extract int from JSONValue dict with type checking."""
    if isinstance(data, dict) and key in data:
        value = data[key]
        if isinstance(value, int):
            return value
        elif isinstance(value, float):
            return int(value)
    return default


def _safe_get_dict(
    data: JSONValue, key: str, default: dict[str, JSONValue] | None = None
) -> dict[str, JSONValue]:
    """Safely extract dict from JSONValue dict with type checking."""
    if default is None:
        default = {}
    if isinstance(data, dict) and key in data:
        value = data[key]
        if isinstance(value, dict):
            return value
    return default


from shared.models.patterns import (
    ApplicationPriority,
    ApplicationRecord,
    ContextFeatures,
    CrossSessionData,
    LearningEffectiveness,
    LearningRecommendation,
    PatternMatch,
    PatternMatchSummary,
    PatternType,
)

logger = logging.getLogger(__name__)


class CrossSessionLearner(BaseTool):  # type: ignore[misc]
    """
    Applies learnings from previous sessions to current context.

    This tool:
    - Retrieves relevant patterns from VectorStore
    - Matches current context with historical successful patterns
    - Provides recommendations based on past experiences
    - Tracks learning application effectiveness
    - Builds institutional memory across sessions
    """

    current_context: str = Field(
        ..., description="JSON string describing current situation/context"
    )
    learning_types: str = Field(
        default="all",
        description="Types of learnings to apply: 'patterns', 'optimizations', 'error_resolutions', 'all'",
    )
    similarity_threshold: float = Field(
        default=0.7, description="Minimum similarity score for pattern matching"
    )
    max_recommendations: int = Field(
        default=5, description="Maximum number of recommendations to provide"
    )
    confidence_threshold: float = Field(
        default=0.6, description="Minimum confidence for learning applications"
    )

    def run(self) -> str:
        try:
            # Parse current context
            context_data = json.loads(self.current_context)

            # Load and initialize learning systems
            learning_results = self._load_historical_learnings()

            if not learning_results.total_learnings:
                return json.dumps(
                    {
                        "status": "no_learnings",
                        "message": "No historical learnings found to apply",
                        "suggestions": [
                            "Continue operating to build learning base",
                            "Ensure learning storage is functioning",
                            "Check VectorStore integration",
                        ],
                    },
                    indent=2,
                )

            # Find relevant patterns for current context
            relevant_patterns = self._find_relevant_patterns(context_data, learning_results)

            # Generate recommendations based on patterns
            recommendations = self._generate_recommendations(context_data, relevant_patterns)

            # Calculate confidence scores and filter
            filtered_recommendations = self._filter_by_confidence(recommendations)

            # Track application for learning feedback
            application_record = self._create_application_record(
                context_data, filtered_recommendations
            )

            # Convert typed objects to dict for JSON serialization
            result = {
                "application_timestamp": datetime.now().isoformat(),
                "context_analyzed": context_data,
                "learning_summary": {
                    "total_learnings_available": learning_results.total_learnings,
                    "relevant_patterns_found": len(relevant_patterns),
                    "recommendations_generated": len(filtered_recommendations),
                },
                "recommendations": [rec.model_dump() for rec in filtered_recommendations],
                "pattern_matches": self._summarize_pattern_matches(relevant_patterns).model_dump(),
                "application_tracking": application_record.model_dump(),
                "learning_effectiveness": self._calculate_learning_effectiveness().model_dump(),
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in cross-session learning application: {e}")
            return json.dumps(
                {
                    "error": f"Cross-session learning failed: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                },
                indent=2,
            )

    def _load_historical_learnings(self) -> CrossSessionData:
        """Load historical learnings from various sources."""
        learning_results = CrossSessionData(learnings=[], total_learnings=0, sources=[])

        try:
            # Load from VectorStore
            vector_learnings = self._load_from_vector_store()
            learning_results.learnings.extend(vector_learnings)
            learning_results.sources.append("vector_store")

            # Load from session transcripts
            session_learnings = self._load_from_session_transcripts()
            learning_results.learnings.extend(session_learnings)
            learning_results.sources.append("session_transcripts")

            # Load from learning storage files
            stored_learnings = self._load_from_learning_storage()
            learning_results.learnings.extend(stored_learnings)
            learning_results.sources.append("learning_storage")

            learning_results.total_learnings = len(learning_results.learnings)

            logger.info(
                f"Loaded {learning_results.total_learnings} historical learnings from {len(learning_results.sources)} sources"
            )

        except Exception as e:
            logger.warning(f"Error loading historical learnings: {e}")

        return learning_results

    def _load_from_vector_store(self) -> list[dict[str, JSONValue]]:
        """Load learnings from VectorStore."""
        learnings = []

        try:
            # This would integrate with the actual VectorStore
            # For now, we'll simulate loading from a VectorStore

            # Search for learning objects
            from agency_memory import VectorStore

            vector_store = VectorStore()

            # Search for different types of learnings
            search_queries = [
                "successful pattern learning optimization",
                "error resolution pattern effective",
                "tool usage pattern high success",
                "workflow optimization improvement",
            ]

            for query in search_queries:
                try:
                    results = vector_store.search(query, limit=20)
                    for result in results:
                        if self._is_learning_object(result):
                            learnings.append(result)
                except Exception as e:
                    logger.warning(f"Error searching VectorStore with query '{query}': {e}")

        except Exception as e:
            logger.warning(f"Error loading from VectorStore: {e}")

        return learnings

    def _load_from_session_transcripts(self) -> list[dict[str, JSONValue]]:
        """Load learnings from session transcript analysis."""
        learnings: list[dict[str, JSONValue]] = []

        try:
            sessions_dir = os.path.join(os.getcwd(), "logs", "sessions")
            if not os.path.exists(sessions_dir):
                return learnings

            # Look for recent session files
            cutoff_date = datetime.now() - timedelta(days=30)  # Last 30 days

            for filename in os.listdir(sessions_dir):
                if filename.endswith(".md"):
                    filepath = os.path.join(sessions_dir, filename)
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))

                    if file_mtime >= cutoff_date:
                        session_learnings = self._extract_learnings_from_transcript(filepath)
                        learnings.extend(session_learnings)

        except Exception as e:
            logger.warning(f"Error loading from session transcripts: {e}")

        return learnings

    def _load_from_learning_storage(self) -> list[dict[str, JSONValue]]:
        """Load learnings from dedicated learning storage files."""
        learnings: list[dict[str, JSONValue]] = []

        try:
            learning_dir = os.path.join(os.getcwd(), "logs", "learnings")
            if not os.path.exists(learning_dir):
                return learnings

            for filename in os.listdir(learning_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(learning_dir, filename)
                    try:
                        with open(filepath) as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                learnings.extend(data)
                            elif isinstance(data, dict):
                                learnings.append(data)
                    except Exception as e:
                        logger.warning(f"Error loading learning file {filepath}: {e}")

        except Exception as e:
            logger.warning(f"Error loading from learning storage: {e}")

        return learnings

    def _extract_learnings_from_transcript(self, filepath: str) -> list[dict[str, JSONValue]]:
        """Extract learning-relevant information from session transcript."""
        learnings: list[dict[str, JSONValue]] = []

        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()

            # Look for learning indicators
            lines = content.split("\n")
            learning_contexts: list[dict[str, JSONValue]] = []

            for i, line in enumerate(lines):
                if any(
                    keyword in line.lower()
                    for keyword in [
                        "successful",
                        "resolved",
                        "optimized",
                        "improved",
                        "pattern",
                        "learning",
                    ]
                ):
                    # Extract context around the learning
                    context_start = max(0, i - 2)
                    context_end = min(len(lines), i + 3)
                    context = "\n".join(lines[context_start:context_end])

                    learning_contexts.append(
                        {
                            "source": "session_transcript",
                            "file": os.path.basename(filepath),
                            "content": context,
                            "line_number": i,
                            "type": "session_learning",
                            "extracted_timestamp": datetime.now().isoformat(),
                        }
                    )

            learnings.extend(learning_contexts)

        except Exception as e:
            logger.warning(f"Error extracting from transcript {filepath}: {e}")

        return learnings

    def _is_learning_object(self, obj: dict[str, JSONValue]) -> bool:
        """Check if object is a structured learning object."""
        learning_indicators = ["learning_id", "pattern", "actionable_insight", "confidence"]
        return any(indicator in obj for indicator in learning_indicators)

    def _find_relevant_patterns(
        self, context_data: dict[str, JSONValue], learning_results: CrossSessionData
    ) -> list[dict[str, JSONValue]]:
        """Find patterns relevant to current context."""
        relevant_patterns = []

        try:
            # Extract key context features
            context_features = self._extract_context_features(context_data)

            # Score each learning for relevance
            for learning in learning_results.learnings:
                relevance_score = self._calculate_relevance_score(context_features, learning)

                if relevance_score >= self.similarity_threshold:
                    pattern_id = _safe_get_str(learning, "learning_id") or _safe_get_str(
                        learning, "pattern_id", "unknown"
                    )
                    pattern_match = PatternMatch(
                        pattern_id=pattern_id,
                        relevance_score=relevance_score,
                        match_reason=self._explain_match_reason(context_features, learning),
                        matched_features=context_features,
                        pattern_type=PatternType.GENERAL,  # Default, could be refined based on learning content
                    )
                    # Store original learning data as dict for backward compatibility
                    pattern_match_dict = pattern_match.model_dump()
                    pattern_match_dict.update(learning)  # Merge original learning data
                    relevant_patterns.append(pattern_match_dict)

            # Sort by relevance score
            relevant_patterns.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

            logger.info(f"Found {len(relevant_patterns)} relevant patterns for current context")

        except Exception as e:
            logger.warning(f"Error finding relevant patterns: {e}")

        return relevant_patterns

    def _extract_context_features(self, context_data: dict[str, JSONValue]) -> ContextFeatures:
        """Extract key features from current context."""
        features = ContextFeatures(
            keywords=[],
            context_type="unknown",
            urgency="normal",
            domain="general",
            agents_involved=[],
            tools_used=[],
            error_types=[],
        )

        try:
            # Extract keywords from all text content
            all_text = []

            def extract_text_recursive(obj):
                if isinstance(obj, str):
                    all_text.append(obj.lower())
                elif isinstance(obj, dict):
                    for value in obj.values():
                        extract_text_recursive(value)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_text_recursive(item)

            extract_text_recursive(context_data)

            # Extract keywords
            combined_text = " ".join(all_text)
            keywords = [word for word in combined_text.split() if len(word) > 3]
            features.keywords = keywords

            # Determine context type
            if any(word in combined_text for word in ["error", "fail", "exception"]):
                features.context_type = "error_handling"
            elif any(word in combined_text for word in ["optimize", "performance", "slow"]):
                features.context_type = "optimization"
            elif any(word in combined_text for word in ["trigger", "self-healing", "automatic"]):
                features.context_type = "self_healing"
            elif any(word in combined_text for word in ["agent", "handoff", "communication"]):
                features.context_type = "agent_interaction"

            # Extract urgency indicators
            if any(word in combined_text for word in ["urgent", "critical", "emergency"]):
                features.urgency = "high"
            elif any(word in combined_text for word in ["low", "background", "routine"]):
                features.urgency = "low"

            # Extract tool names
            common_tools = ["read", "write", "edit", "grep", "bash", "todowrite"]
            features.tools_used = [tool for tool in common_tools if tool in combined_text]

            # Extract agent names
            common_agents = ["planner", "coder", "auditor", "learning", "chief"]
            features.agents_involved = [agent for agent in common_agents if agent in combined_text]

        except Exception as e:
            logger.warning(f"Error extracting context features: {e}")

        return features

    def _calculate_relevance_score(
        self, context_features: ContextFeatures, learning: dict[str, JSONValue]
    ) -> float:
        """Calculate relevance score between context and learning."""
        try:
            score = 0.0
            weights = {
                "keyword_overlap": 0.4,
                "context_type_match": 0.3,
                "tool_match": 0.15,
                "agent_match": 0.1,
                "learning_confidence": 0.05,
            }

            # Keyword overlap score
            content = _safe_get_str(learning, "content")
            description = _safe_get_str(learning, "description")
            insight = _safe_get_str(learning, "actionable_insight")
            learning_text = (content + " " + description + " " + insight).lower()
            learning_keywords = set(word for word in learning_text.split() if len(word) > 3)

            if context_features.keywords and learning_keywords:
                context_keywords_set = set(context_features.keywords)
                overlap = context_keywords_set.intersection(learning_keywords)
                keyword_score = len(overlap) / len(context_keywords_set.union(learning_keywords))
                score += keyword_score * weights["keyword_overlap"]

            # Context type match
            learning_type = (
                _safe_get_str(learning, "type") or _safe_get_str(learning, "category")
            ).lower()
            if (
                context_features.context_type in learning_type
                or learning_type in context_features.context_type
            ):
                score += 1.0 * weights["context_type_match"]

            # Tool match
            learning_tools = self._extract_tools_from_learning(learning)
            tool_overlap = set(context_features.tools_used).intersection(learning_tools)
            if context_features.tools_used and learning_tools:
                tool_score = len(tool_overlap) / len(
                    set(context_features.tools_used).union(learning_tools)
                )
                score += tool_score * weights["tool_match"]

            # Agent match
            learning_agents = self._extract_agents_from_learning(learning)
            agent_overlap = set(context_features.agents_involved).intersection(learning_agents)
            if context_features.agents_involved and learning_agents:
                agent_score = len(agent_overlap) / len(
                    set(context_features.agents_involved).union(learning_agents)
                )
                score += agent_score * weights["agent_match"]

            # Learning confidence bonus
            learning_confidence = learning.get(
                "confidence", learning.get("overall_confidence", 0.5)
            )
            score += learning_confidence * weights["learning_confidence"]

            return min(1.0, score)  # Cap at 1.0

        except Exception as e:
            logger.warning(f"Error calculating relevance score: {e}")
            return 0.0

    def _extract_tools_from_learning(self, learning: dict[str, JSONValue]) -> set:
        """Extract tool names from learning object."""
        tools = set()

        learning_text = str(learning).lower()
        common_tools = ["read", "write", "edit", "grep", "bash", "todowrite", "glob"]

        for tool in common_tools:
            if tool in learning_text:
                tools.add(tool)

        return tools

    def _extract_agents_from_learning(self, learning: dict[str, JSONValue]) -> set:
        """Extract agent names from learning object."""
        agents = set()

        learning_text = str(learning).lower()
        common_agents = ["planner", "coder", "auditor", "learning", "chief", "test_generator"]

        for agent in common_agents:
            if agent in learning_text:
                agents.add(agent)

        return agents

    def _explain_match_reason(
        self, context_features: ContextFeatures, learning: dict[str, JSONValue]
    ) -> str:
        """Explain why a learning was matched to the context."""
        reasons = []

        # Check keyword overlap
        learning_text = str(learning.get("content", "")).lower()
        learning_keywords = set(word for word in learning_text.split() if len(word) > 3)
        context_keywords_set = set(context_features.keywords)
        overlap = context_keywords_set.intersection(learning_keywords)

        if overlap:
            reasons.append(f"Keyword overlap: {', '.join(list(overlap)[:3])}")

        # Check context type
        learning_type = learning.get("type", "").lower()
        if context_features.context_type in learning_type:
            reasons.append(f"Context type match: {context_features.context_type}")

        # Check tools
        learning_tools = self._extract_tools_from_learning(learning)
        tool_overlap = set(context_features.tools_used).intersection(learning_tools)
        if tool_overlap:
            reasons.append(f"Tool match: {', '.join(tool_overlap)}")

        return "; ".join(reasons) if reasons else "General similarity"

    def _generate_recommendations(
        self, context_data: dict[str, JSONValue], relevant_patterns: list[dict[str, JSONValue]]
    ) -> list[LearningRecommendation]:
        """Generate actionable recommendations from relevant patterns."""
        recommendations = []

        try:
            # Group patterns by type for better recommendations
            pattern_groups = defaultdict(list)
            for pattern in relevant_patterns[
                : self.max_recommendations * 2
            ]:  # Get extra for filtering
                pattern_type = pattern.get("type", pattern.get("category", "general"))
                pattern_groups[pattern_type].append(pattern)

            # Generate recommendations for each pattern group
            for pattern_type, patterns in pattern_groups.items():
                group_recommendation = self._create_group_recommendation(
                    pattern_type, patterns, context_data
                )
                if group_recommendation:
                    recommendations.append(group_recommendation)

            # Generate individual high-confidence recommendations
            for pattern in relevant_patterns[: self.max_recommendations]:
                if pattern.get("relevance_score", 0) > 0.8:
                    individual_recommendation = self._create_individual_recommendation(
                        pattern, context_data
                    )
                    if individual_recommendation:
                        recommendations.append(individual_recommendation)

            # Remove duplicates and sort by confidence
            recommendations = self._deduplicate_recommendations(recommendations)
            recommendations.sort(
                key=lambda x: x.confidence if hasattr(x, "confidence") else x.get("confidence", 0),
                reverse=True,
            )

        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")

        return recommendations[: self.max_recommendations]

    def _create_group_recommendation(
        self,
        pattern_type: str,
        patterns: list[dict[str, JSONValue]],
        context_data: dict[str, JSONValue],
    ) -> LearningRecommendation | None:
        """Create recommendation based on a group of similar patterns."""
        try:
            if len(patterns) < 2:
                return None

            avg_relevance = sum(p.get("relevance_score", 0) for p in patterns) / len(patterns)
            avg_confidence = sum(
                p.get("confidence", p.get("overall_confidence", 0.5)) for p in patterns
            ) / len(patterns)

            # Extract common actionable insights
            common_insights = self._extract_common_insights(patterns)

            priority_str = self._determine_priority(avg_confidence, avg_relevance, len(patterns))
            priority = ApplicationPriority(priority_str)

            # Map pattern_type to PatternType enum
            try:
                pattern_type_enum = PatternType(pattern_type)
            except ValueError:
                pattern_type_enum = PatternType.GENERAL

            recommendation = LearningRecommendation(
                recommendation_id=f"group_{pattern_type}_{int(datetime.now().timestamp())}",
                type="pattern_group",
                pattern_type=pattern_type_enum,
                title=f"Apply {pattern_type.title()} Best Practices",
                description=f"Based on {len(patterns)} similar successful patterns",
                actionable_steps=common_insights,
                confidence=min(0.9, avg_confidence * avg_relevance),
                supporting_patterns=len(patterns),
                evidence=patterns[:2],  # Top 2 as evidence
                expected_benefit="Improved success rate and efficiency",
                application_priority=priority,
            )

            return recommendation

        except Exception as e:
            logger.warning(f"Error creating group recommendation: {e}")
            return None

    def _create_individual_recommendation(
        self, pattern: dict[str, JSONValue], context_data: dict[str, JSONValue]
    ) -> LearningRecommendation | None:
        """Create recommendation based on individual high-confidence pattern."""
        try:
            actionable_insight = pattern.get("actionable_insight", "")
            if not actionable_insight:
                # Try to extract from description
                actionable_insight = pattern.get(
                    "description", "Apply this pattern to current situation"
                )

            priority_str = self._determine_priority(
                pattern.get("confidence", 0.5), pattern.get("relevance_score", 0), 1
            )
            priority = ApplicationPriority(priority_str)

            recommendation = LearningRecommendation(
                recommendation_id=f"individual_{pattern.get('learning_id', 'unknown')}_{int(datetime.now().timestamp())}",
                type="individual_pattern",
                pattern_id=pattern.get("learning_id", pattern.get("pattern_id", "unknown")),
                title=pattern.get("title", "Apply Successful Pattern"),
                description=pattern.get("description", ""),
                actionable_steps=[actionable_insight] if actionable_insight else [],
                confidence=pattern.get("relevance_score", 0) * pattern.get("confidence", 0.5),
                supporting_patterns=1,
                evidence=[pattern],
                expected_benefit=self._extract_expected_benefit(pattern),
                application_priority=priority,
            )

            return recommendation

        except Exception as e:
            logger.warning(f"Error creating individual recommendation: {e}")
            return None

    def _extract_common_insights(self, patterns: list[dict[str, JSONValue]]) -> list[str]:
        """Extract common actionable insights from patterns."""
        insights = []

        try:
            # Collect all actionable insights
            all_insights = []
            for pattern in patterns:
                insight = pattern.get("actionable_insight", "")
                if insight:
                    all_insights.append(insight.lower())

            # Find common themes (simplified)
            if all_insights:
                # Look for common keywords in insights
                common_words = defaultdict(int)
                for insight in all_insights:
                    words = insight.split()
                    for word in words:
                        if len(word) > 4:  # Ignore short words
                            common_words[word] += 1

                # Extract top themes
                top_themes = sorted(common_words.items(), key=lambda x: x[1], reverse=True)[:3]

                if top_themes:
                    insights.append(f"Focus on {', '.join([theme[0] for theme in top_themes])}")

            # Add pattern-specific insights
            for pattern in patterns[:3]:  # Top 3 patterns
                insight = pattern.get("actionable_insight", "")
                if insight and insight not in insights:
                    insights.append(insight)

        except Exception as e:
            logger.warning(f"Error extracting common insights: {e}")

        return insights[:5]  # Limit to 5 insights

    def _extract_expected_benefit(self, pattern: dict[str, JSONValue]) -> str:
        """Extract expected benefit from pattern."""
        # Look for success metrics or expected improvements
        success_metrics = pattern.get("success_metrics", [])
        if success_metrics:
            return f"Expected: {success_metrics[0]}"

        # Check for effectiveness score
        effectiveness = pattern.get("effectiveness_score", 0)
        if effectiveness > 0:
            return f"Expected {effectiveness:.0%} improvement"

        # Default benefit
        return "Improved success rate based on historical pattern"

    def _determine_priority(self, confidence: float, relevance: float, support_count: int) -> str:
        """Determine application priority for recommendation."""
        combined_score = confidence * 0.4 + relevance * 0.4 + min(1.0, support_count / 5) * 0.2

        if combined_score > 0.8:
            return "high"
        elif combined_score > 0.6:
            return "medium"
        else:
            return "low"

    def _deduplicate_recommendations(
        self, recommendations: list[LearningRecommendation]
    ) -> list[LearningRecommendation]:
        """Remove duplicate recommendations."""
        seen_titles = set()
        deduplicated = []

        for rec in recommendations:
            title = rec.title
            if title not in seen_titles:
                seen_titles.add(title)
                deduplicated.append(rec)

        return deduplicated

    def _filter_by_confidence(
        self, recommendations: list[LearningRecommendation]
    ) -> list[LearningRecommendation]:
        """Filter recommendations by confidence threshold."""
        return [rec for rec in recommendations if rec.confidence >= self.confidence_threshold]

    def _summarize_pattern_matches(
        self, relevant_patterns: list[dict[str, JSONValue]]
    ) -> PatternMatchSummary:
        """Summarize how patterns matched to current context."""
        match_types = defaultdict(int)
        top_matches = []
        average_relevance = 0.0

        try:
            if relevant_patterns:
                average_relevance = sum(
                    p.get("relevance_score", 0) for p in relevant_patterns
                ) / len(relevant_patterns)

                # Count match types
                for pattern in relevant_patterns:
                    pattern_type = pattern.get("type", pattern.get("category", "unknown"))
                    match_types[pattern_type] += 1

                # Get top matches
                top_matches = [
                    {
                        "pattern_id": p.get("learning_id", p.get("pattern_id", "unknown")),
                        "relevance_score": p.get("relevance_score", 0),
                        "match_reason": p.get("match_reason", ""),
                        "type": p.get("type", "unknown"),
                    }
                    for p in relevant_patterns[:3]
                ]

            summary = PatternMatchSummary(
                total_matches=len(relevant_patterns),
                average_relevance=average_relevance,
                match_types=dict(match_types),
                top_matches=top_matches,
            )

        except Exception as e:
            logger.warning(f"Error summarizing pattern matches: {e}")
            # Return default summary on error
            summary = PatternMatchSummary(
                total_matches=0, average_relevance=0.0, match_types={}, top_matches=[]
            )

        return summary

    def _create_application_record(
        self, context_data: dict[str, JSONValue], recommendations: list[LearningRecommendation]
    ) -> ApplicationRecord:
        """Create record for tracking learning application effectiveness."""
        record = ApplicationRecord(
            application_id=f"cross_session_app_{int(datetime.now().timestamp())}",
            timestamp=datetime.now(),
            context_summary=self._summarize_context(context_data),
            recommendations_count=len(recommendations),
            recommendation_ids=[rec.recommendation_id for rec in recommendations],
            average_confidence=sum(rec.confidence for rec in recommendations) / len(recommendations)
            if recommendations
            else 0,
            learning_types_applied=list(set(rec.type for rec in recommendations)),
            status="applied",
            feedback_pending=True,
        )

        return record

    def _summarize_context(self, context_data: dict[str, JSONValue]) -> str:
        """Create brief summary of context for tracking."""
        try:
            # Extract key elements
            key_elements = []

            if "task" in context_data:
                key_elements.append(f"Task: {context_data['task']}")
            if "agent" in context_data:
                key_elements.append(f"Agent: {context_data['agent']}")
            if "tools" in context_data:
                key_elements.append(f"Tools: {', '.join(context_data['tools'][:3])}")

            return "; ".join(key_elements) if key_elements else "General context application"

        except Exception:
            return "Context summary unavailable"

    def _calculate_learning_effectiveness(self) -> LearningEffectiveness:
        """Calculate effectiveness of previous learning applications."""
        try:
            # This would track effectiveness over time
            # For now, return placeholder metrics
            return LearningEffectiveness(
                total_applications=0,  # Would track actual applications
                successful_applications=0,  # Would track successful applications
                success_rate=0.0,  # Would track success feedback
                improvement_measured=False,
                last_effectiveness_update=datetime.now(),
                trend_direction="unknown",
            )

        except Exception as e:
            logger.warning(f"Error calculating learning effectiveness: {e}")
            # Return default effectiveness with error logged
            logger.error(f"Error in effectiveness calculation: {e}")
            return LearningEffectiveness(
                total_applications=0,
                successful_applications=0,
                success_rate=0.0,
                improvement_measured=False,
                last_effectiveness_update=datetime.now(),
                trend_direction="unknown",
            )
