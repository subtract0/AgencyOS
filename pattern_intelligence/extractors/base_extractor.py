"""
Base pattern extractor interface and common functionality.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ..coding_pattern import CodingPattern, ProblemContext, SolutionApproach, EffectivenessMetric, PatternMetadata

logger = logging.getLogger(__name__)


class BasePatternExtractor(ABC):
    """Base class for all pattern extractors."""

    def __init__(self, source_name: str, confidence_threshold: float = 0.5):
        """
        Initialize pattern extractor.

        Args:
            source_name: Name of the source (e.g., "local_codebase", "github")
            confidence_threshold: Minimum confidence for extracted patterns
        """
        self.source_name = source_name
        self.confidence_threshold = confidence_threshold
        self.extracted_patterns: List[CodingPattern] = []

    @abstractmethod
    def extract_patterns(self, **kwargs) -> List[CodingPattern]:
        """
        Extract patterns from the source.

        Returns:
            List of discovered coding patterns
        """
        pass

    def create_pattern(
        self,
        context: ProblemContext,
        solution: SolutionApproach,
        outcome: EffectivenessMetric,
        source_reference: str,
        tags: List[str] = None
    ) -> CodingPattern:
        """
        Create a standardized CodingPattern.

        Args:
            context: Problem context
            solution: Solution approach
            outcome: Effectiveness metrics
            source_reference: Reference to source (commit, file, etc.)
            tags: Additional categorization tags

        Returns:
            CodingPattern instance
        """
        tags = tags or []
        tags.extend([self.source_name, context.domain])

        metadata = PatternMetadata(
            pattern_id="",  # Will be auto-generated
            discovered_timestamp=datetime.now().isoformat(),
            source=f"{self.source_name}:{source_reference}",
            discoverer=self.__class__.__name__,
            tags=tags,
        )

        return CodingPattern(
            context=context,
            solution=solution,
            outcome=outcome,
            metadata=metadata
        )

    def validate_pattern(self, pattern: CodingPattern) -> bool:
        """
        Validate that a pattern meets quality thresholds.

        Args:
            pattern: Pattern to validate

        Returns:
            True if pattern is valid
        """
        # Check confidence threshold
        if pattern.outcome.confidence < self.confidence_threshold:
            return False

        # Check effectiveness threshold
        if pattern.outcome.effectiveness_score() < 0.3:
            return False

        # Check required fields
        if not pattern.context.description or not pattern.solution.approach:
            return False

        # Check for meaningful content
        if len(pattern.context.description.split()) < 3:
            return False

        if len(pattern.solution.approach.split()) < 3:
            return False

        return True

    def extract_and_validate(self, **kwargs) -> List[CodingPattern]:
        """
        Extract patterns and validate them.

        Returns:
            List of validated patterns
        """
        try:
            # Extract raw patterns
            raw_patterns = self.extract_patterns(**kwargs)
            logger.info(f"{self.source_name}: Extracted {len(raw_patterns)} raw patterns")

            # Validate patterns
            validated_patterns = []
            for pattern in raw_patterns:
                if self.validate_pattern(pattern):
                    pattern.metadata.validation_status = "validated"
                    validated_patterns.append(pattern)
                else:
                    logger.debug(f"Pattern failed validation: {pattern.metadata.pattern_id}")

            self.extracted_patterns = validated_patterns
            logger.info(f"{self.source_name}: Validated {len(validated_patterns)} patterns")

            return validated_patterns

        except Exception as e:
            logger.error(f"{self.source_name}: Pattern extraction failed: {e}")
            return []

    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get statistics about extracted patterns."""
        if not self.extracted_patterns:
            return {"total_patterns": 0, "message": "No patterns extracted yet"}

        patterns = self.extracted_patterns

        # Calculate statistics
        domains = [p.context.domain for p in patterns]
        domain_counts = {}
        for domain in domains:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

        effectiveness_scores = [p.outcome.effectiveness_score() for p in patterns]
        success_rates = [p.outcome.success_rate for p in patterns]

        return {
            "source": self.source_name,
            "total_patterns": len(patterns),
            "domains": domain_counts,
            "average_effectiveness": sum(effectiveness_scores) / len(effectiveness_scores),
            "average_success_rate": sum(success_rates) / len(success_rates),
            "confidence_threshold": self.confidence_threshold,
            "extraction_timestamp": datetime.now().isoformat(),
        }

    def filter_patterns(
        self,
        domain: str = None,
        min_effectiveness: float = None,
        tags: List[str] = None
    ) -> List[CodingPattern]:
        """
        Filter extracted patterns by criteria.

        Args:
            domain: Filter by problem domain
            min_effectiveness: Minimum effectiveness score
            tags: Required tags

        Returns:
            Filtered list of patterns
        """
        filtered_patterns = self.extracted_patterns

        if domain:
            filtered_patterns = [p for p in filtered_patterns if p.context.domain == domain]

        if min_effectiveness is not None:
            filtered_patterns = [p for p in filtered_patterns
                               if p.outcome.effectiveness_score() >= min_effectiveness]

        if tags:
            tag_set = set(tags)
            filtered_patterns = [p for p in filtered_patterns
                               if tag_set.intersection(set(p.metadata.tags))]

        return filtered_patterns

    def analyze_success_factors(self) -> Dict[str, Any]:
        """Analyze what makes patterns successful."""
        if not self.extracted_patterns:
            return {"message": "No patterns to analyze"}

        patterns = self.extracted_patterns

        # Group by effectiveness
        high_effectiveness = [p for p in patterns if p.outcome.effectiveness_score() >= 0.8]
        medium_effectiveness = [p for p in patterns if 0.5 <= p.outcome.effectiveness_score() < 0.8]
        low_effectiveness = [p for p in patterns if p.outcome.effectiveness_score() < 0.5]

        # Analyze tools used
        all_tools = []
        for pattern in patterns:
            all_tools.extend(pattern.solution.tools)

        tool_counts = {}
        for tool in all_tools:
            tool_counts[tool] = tool_counts.get(tool, 0) + 1

        # Most common tools in high-effectiveness patterns
        high_eff_tools = []
        for pattern in high_effectiveness:
            high_eff_tools.extend(pattern.solution.tools)

        high_eff_tool_counts = {}
        for tool in high_eff_tools:
            high_eff_tool_counts[tool] = high_eff_tool_counts.get(tool, 0) + 1

        return {
            "total_patterns": len(patterns),
            "effectiveness_distribution": {
                "high": len(high_effectiveness),
                "medium": len(medium_effectiveness),
                "low": len(low_effectiveness),
            },
            "most_common_tools": sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "high_effectiveness_tools": sorted(high_eff_tool_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "success_indicators": self._identify_success_indicators(high_effectiveness),
        }

    def _identify_success_indicators(self, successful_patterns: List[CodingPattern]) -> List[str]:
        """Identify common characteristics of successful patterns."""
        indicators = []

        if not successful_patterns:
            return indicators

        # Common domains
        domains = [p.context.domain for p in successful_patterns]
        most_common_domain = max(set(domains), key=domains.count)
        if domains.count(most_common_domain) >= len(successful_patterns) * 0.3:
            indicators.append(f"Domain '{most_common_domain}' shows high success rate")

        # Common tools
        all_tools = []
        for pattern in successful_patterns:
            all_tools.extend(pattern.solution.tools)

        if all_tools:
            most_common_tool = max(set(all_tools), key=all_tools.count)
            indicators.append(f"Tool '{most_common_tool}' frequently used in successful patterns")

        # Common constraints
        all_constraints = []
        for pattern in successful_patterns:
            all_constraints.extend(pattern.context.constraints)

        if all_constraints:
            most_common_constraint = max(set(all_constraints), key=all_constraints.count)
            indicators.append(f"Constraint '{most_common_constraint}' common in successful patterns")

        # Success rate patterns
        high_success_rate_patterns = [p for p in successful_patterns if p.outcome.success_rate >= 0.9]
        if len(high_success_rate_patterns) >= len(successful_patterns) * 0.5:
            indicators.append("High success rate (>90%) correlates with effectiveness")

        return indicators