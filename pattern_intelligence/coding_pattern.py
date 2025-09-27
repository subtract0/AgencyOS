# mypy: disable-error-code="misc,assignment,arg-type,attr-defined,index,return-value,union-attr,dict-item,operator"
"""
Core CodingPattern data structure and related types.

The fundamental building block of the Infinite Intelligence Amplifier.
A CodingPattern captures reusable problem-solving wisdom in a structured format
that enables semantic search, application, and continuous improvement.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, cast
from shared.type_definitions.json import JSONValue
from datetime import datetime
import hashlib
import json


def _safe_get_str(data: JSONValue, key: str, default: str = "") -> str:
    """Safely extract string from JSONValue dict with type checking."""
    if isinstance(data, dict) and key in data:
        value = data[key]
        if isinstance(value, str):
            return value
    return default


def _safe_get_list(data: JSONValue, key: str, default: Optional[List[str]] = None) -> List[str]:
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


def _safe_get_optional_str(data: JSONValue, key: str) -> Optional[str]:
    """Safely extract optional string from JSONValue dict with type checking."""
    if isinstance(data, dict) and key in data:
        value = data[key]
        if isinstance(value, str):
            return value
    return None


@dataclass
class ProblemContext:
    """Context describing the problem that triggered this pattern."""

    description: str  # Clear problem description
    domain: str  # Problem domain (e.g., "error_handling", "performance", "architecture")
    constraints: List[str] = field(default_factory=list)  # Constraints that shaped the solution
    symptoms: List[str] = field(default_factory=list)  # Observable symptoms of the problem
    scale: Optional[str] = None  # Scale/scope (e.g., "1000+ users", "10MB+ files")
    urgency: Optional[str] = None  # Urgency level ("critical", "medium", "low")

    def to_searchable_text(self) -> str:
        """Convert to text for semantic search."""
        parts = [self.description, self.domain]
        parts.extend(self.constraints)
        parts.extend(self.symptoms)
        if self.scale:
            parts.append(self.scale)
        if self.urgency:
            parts.append(self.urgency)
        return " ".join(parts)


@dataclass
class SolutionApproach:
    """Solution approach and implementation details."""

    approach: str  # High-level approach description
    implementation: str  # Specific implementation details
    tools: List[str] = field(default_factory=list)  # Tools/technologies used
    reasoning: str = ""  # Reasoning behind this approach
    code_examples: List[str] = field(default_factory=list)  # Code snippets
    dependencies: List[str] = field(default_factory=list)  # External dependencies
    alternatives: List[str] = field(default_factory=list)  # Alternative approaches considered

    def to_searchable_text(self) -> str:
        """Convert to text for semantic search."""
        parts = [self.approach, self.implementation, self.reasoning]
        parts.extend(self.tools)
        parts.extend(self.alternatives)
        return " ".join(parts)


@dataclass
class EffectivenessMetric:
    """Measured outcomes and effectiveness of the solution."""

    success_rate: float  # Success rate (0.0 to 1.0)
    performance_impact: Optional[str] = None  # Performance improvement description
    maintainability_impact: Optional[str] = None  # Impact on code maintainability
    user_impact: Optional[str] = None  # Impact on users/stakeholders
    technical_debt: Optional[str] = None  # Technical debt impact
    adoption_rate: int = 0  # How many times this pattern has been seen/used
    longevity: Optional[str] = None  # How long the pattern has remained effective
    confidence: float = 0.5  # Confidence in these metrics (0.0 to 1.0)

    def effectiveness_score(self) -> float:
        """Calculate overall effectiveness score."""
        base_score = self.success_rate * self.confidence

        # Boost for proven adoption
        adoption_boost = min(0.2, self.adoption_rate / 100)

        # Boost for measurable impacts
        impact_boost = 0.1 if (self.performance_impact or
                              self.maintainability_impact or
                              self.user_impact) else 0.0

        return min(1.0, base_score + adoption_boost + impact_boost)


@dataclass
class PatternMetadata:
    """Metadata about pattern discovery and application."""

    pattern_id: str
    discovered_timestamp: str
    source: str  # Where pattern was discovered (e.g., "github:repo/commit", "session:id")
    discoverer: str = "pattern_extractor"  # What extracted this pattern
    last_applied: Optional[str] = None  # When last successfully applied
    application_count: int = 0  # How many times applied
    validation_status: str = "unvalidated"  # "validated", "unvalidated", "deprecated"
    tags: List[str] = field(default_factory=list)  # Categorization tags
    related_patterns: List[str] = field(default_factory=list)  # Related pattern IDs

    @classmethod
    def generate_id(cls, context: ProblemContext, solution: SolutionApproach) -> str:
        """Generate unique pattern ID from content."""
        content = f"{context.description}{context.domain}{solution.approach}"
        hash_obj = hashlib.md5(content.encode())
        timestamp = int(datetime.now().timestamp())
        return f"pattern_{hash_obj.hexdigest()[:8]}_{timestamp}"


@dataclass
class CodingPattern:
    """
    A reusable coding pattern capturing problem-solution-outcome wisdom.

    The core data structure of the Infinite Intelligence Amplifier.
    Enables semantic search, automatic application, and continuous improvement.
    """

    context: ProblemContext
    solution: SolutionApproach
    outcome: EffectivenessMetric
    metadata: PatternMetadata

    def __post_init__(self):
        """Generate pattern ID if not provided."""
        if not self.metadata.pattern_id:
            self.metadata.pattern_id = PatternMetadata.generate_id(
                self.context, self.solution
            )

    def to_searchable_text(self) -> str:
        """Convert entire pattern to searchable text."""
        context_text = self.context.to_searchable_text()
        solution_text = self.solution.to_searchable_text()

        # Add outcome keywords
        outcome_parts = []
        if self.outcome.performance_impact:
            outcome_parts.append(self.outcome.performance_impact)
        if self.outcome.maintainability_impact:
            outcome_parts.append(self.outcome.maintainability_impact)
        if self.outcome.user_impact:
            outcome_parts.append(self.outcome.user_impact)

        # Add metadata tags
        tag_text = " ".join(self.metadata.tags)

        return f"{context_text} {solution_text} {' '.join(outcome_parts)} {tag_text}"

    def to_dict(self) -> Dict[str, JSONValue]:
        """Convert to dictionary for storage."""
        return {
            "pattern_id": self.metadata.pattern_id,
            "context": {
                "description": self.context.description,
                "domain": self.context.domain,
                "constraints": cast(JSONValue, self.context.constraints),
                "symptoms": cast(JSONValue, self.context.symptoms),
                "scale": self.context.scale,
                "urgency": self.context.urgency,
            },
            "solution": {
                "approach": self.solution.approach,
                "implementation": self.solution.implementation,
                "tools": cast(JSONValue, self.solution.tools),
                "reasoning": self.solution.reasoning,
                "code_examples": cast(JSONValue, self.solution.code_examples),
                "dependencies": cast(JSONValue, self.solution.dependencies),
                "alternatives": cast(JSONValue, self.solution.alternatives),
            },
            "outcome": {
                "success_rate": self.outcome.success_rate,
                "performance_impact": self.outcome.performance_impact,
                "maintainability_impact": self.outcome.maintainability_impact,
                "user_impact": self.outcome.user_impact,
                "technical_debt": self.outcome.technical_debt,
                "adoption_rate": self.outcome.adoption_rate,
                "longevity": self.outcome.longevity,
                "confidence": self.outcome.confidence,
                "effectiveness_score": self.outcome.effectiveness_score(),
            },
            "metadata": {
                "pattern_id": self.metadata.pattern_id,
                "discovered_timestamp": self.metadata.discovered_timestamp,
                "source": self.metadata.source,
                "discoverer": self.metadata.discoverer,
                "last_applied": self.metadata.last_applied,
                "application_count": self.metadata.application_count,
                "validation_status": self.metadata.validation_status,
                "tags": cast(JSONValue, self.metadata.tags),
                "related_patterns": cast(JSONValue, self.metadata.related_patterns),
            },
            "searchable_text": self.to_searchable_text(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, JSONValue]) -> "CodingPattern":
        """Create CodingPattern from dictionary."""
        # Safely extract nested dicts with type checking
        context_data = data.get("context", {})
        solution_data = data.get("solution", {})
        outcome_data = data.get("outcome", {})
        metadata_data = data.get("metadata", {})

        context = ProblemContext(
            description=_safe_get_str(context_data, "description"),
            domain=_safe_get_str(context_data, "domain"),
            constraints=_safe_get_list(context_data, "constraints"),
            symptoms=_safe_get_list(context_data, "symptoms"),
            scale=_safe_get_optional_str(context_data, "scale"),
            urgency=_safe_get_optional_str(context_data, "urgency"),
        )

        solution = SolutionApproach(
            approach=_safe_get_str(solution_data, "approach"),
            implementation=_safe_get_str(solution_data, "implementation"),
            tools=_safe_get_list(solution_data, "tools"),
            reasoning=_safe_get_str(solution_data, "reasoning"),
            code_examples=_safe_get_list(solution_data, "code_examples"),
            dependencies=_safe_get_list(solution_data, "dependencies"),
            alternatives=_safe_get_list(solution_data, "alternatives"),
        )

        outcome = EffectivenessMetric(
            success_rate=_safe_get_float(outcome_data, "success_rate"),
            performance_impact=_safe_get_optional_str(outcome_data, "performance_impact"),
            maintainability_impact=_safe_get_optional_str(outcome_data, "maintainability_impact"),
            user_impact=_safe_get_optional_str(outcome_data, "user_impact"),
            technical_debt=_safe_get_optional_str(outcome_data, "technical_debt"),
            adoption_rate=_safe_get_int(outcome_data, "adoption_rate", 0),
            longevity=_safe_get_optional_str(outcome_data, "longevity"),
            confidence=_safe_get_float(outcome_data, "confidence", 0.5),
        )

        metadata = PatternMetadata(
            pattern_id=_safe_get_str(metadata_data, "pattern_id"),
            discovered_timestamp=_safe_get_str(metadata_data, "discovered_timestamp"),
            source=_safe_get_str(metadata_data, "source"),
            discoverer=_safe_get_str(metadata_data, "discoverer", "pattern_extractor"),
            last_applied=_safe_get_optional_str(metadata_data, "last_applied"),
            application_count=_safe_get_int(metadata_data, "application_count", 0),
            validation_status=_safe_get_str(metadata_data, "validation_status", "unvalidated"),
            tags=_safe_get_list(metadata_data, "tags"),
            related_patterns=_safe_get_list(metadata_data, "related_patterns"),
        )

        return cls(context=context, solution=solution, outcome=outcome, metadata=metadata)

    def matches_context(self, target_context: Union[str, ProblemContext], threshold: float = 0.7) -> bool:
        """Check if this pattern matches a target context."""
        if isinstance(target_context, str):
            # Simple keyword matching for now
            pattern_text = self.to_searchable_text().lower()
            target_text = target_context.lower()

            target_words = set(target_text.split())
            pattern_words = set(pattern_text.split())

            if not target_words:
                return False

            overlap = target_words.intersection(pattern_words)
            similarity = len(overlap) / len(target_words)

            return similarity >= threshold

        elif isinstance(target_context, ProblemContext):
            # More sophisticated matching for ProblemContext objects
            # Check domain match
            if self.context.domain == target_context.domain:
                return True

            # Check description similarity
            return self.matches_context(target_context.description, threshold)

        return False

    def can_be_applied(self, current_constraints: List[str] = None) -> bool:
        """Check if this pattern can be applied given current constraints."""
        current_constraints = current_constraints or []

        # Check if pattern dependencies are available
        # (This would need integration with environment checking)

        # Check if pattern hasn't been deprecated
        if self.metadata.validation_status == "deprecated":
            return False

        # Check effectiveness threshold
        if self.outcome.effectiveness_score() < 0.3:
            return False

        return True

    def get_application_instructions(self) -> str:
        """Get instructions for applying this pattern."""
        instructions = []

        instructions.append(f"Pattern: {self.metadata.pattern_id}")
        instructions.append(f"Context: {self.context.description}")
        instructions.append(f"Approach: {self.solution.approach}")
        instructions.append(f"Implementation: {self.solution.implementation}")

        if self.solution.tools:
            instructions.append(f"Tools needed: {', '.join(self.solution.tools)}")

        if self.solution.dependencies:
            instructions.append(f"Dependencies: {', '.join(self.solution.dependencies)}")

        if self.solution.code_examples:
            instructions.append("Code examples:")
            for i, example in enumerate(self.solution.code_examples, 1):
                instructions.append(f"  {i}. {example}")

        instructions.append(f"Expected success rate: {self.outcome.success_rate:.1%}")

        if self.outcome.performance_impact:
            instructions.append(f"Performance impact: {self.outcome.performance_impact}")

        return "\n".join(instructions)