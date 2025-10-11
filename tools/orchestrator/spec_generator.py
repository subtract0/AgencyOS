"""
SpecGenerator: LLM-powered specification generator with VectorStore learning.

Constitutional Compliance:
- Article IV: Query VectorStore BEFORE generation (mandatory)
- Article V: Spec-kit methodology (Goals, Personas, Success Criteria)
- Law #2: Strict typing with Pydantic models
- Law #5: Result pattern for error handling

Usage:
    from tools.orchestrator.spec_generator import SpecGenerator, SpecIntent, Spec

    context = create_agent_context(session_id="feature_123")
    generator = SpecGenerator(context=context)

    intent = SpecIntent(
        title="JWT Authentication",
        description="Add JWT-based auth to API endpoints",
        priority="high",
        tags=["auth", "security"]
    )

    result = generator.generate(intent)
    if result.is_ok():
        spec = result.unwrap()
        print(spec.goals)
"""

import logging
from typing import Any

from pydantic import BaseModel, Field, field_validator

from shared.agent_context import AgentContext
from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)


class SpecMetadata(BaseModel):
    """
    Metadata for specification (priority, tags, etc.).

    Constitutional Compliance:
        - Law #2: No Dict[Any, Any] - use typed Pydantic model
    """

    priority: str = Field(default="medium", description="Priority level")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    estimated_complexity: str = Field(default="moderate", description="Estimated complexity")
    related_specs: list[str] = Field(default_factory=list, description="Related specification IDs")


class SpecIntent(BaseModel):
    """
    User intent for feature specification generation.

    Captures high-level WHAT/WHY before tactical HOW/WHEN planning.
    Feeds into SpecGenerator to produce formal specification.

    Note: Different from IntentParser.Intent which is for parsing input modes.
    This SpecIntent is specifically for spec-kit template generation.

    Constitutional Compliance:
        - Law #2: Strict typing (no Dict[Any, Any])
        - Law #3: Input validation with Pydantic
    """

    title: str = Field(..., min_length=1, description="Feature title")
    description: str = Field(..., min_length=1, description="Feature description")
    priority: str = Field(default="medium", description="Priority: low, medium, high, critical")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")

    @field_validator("title", "description")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate title and description are non-empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class Spec(BaseModel):
    """
    Formal specification following spec-kit methodology.

    Spec-kit template sections (Article V):
    - Goals: What the feature WILL accomplish
    - Personas: Who uses this feature and why
    - Success Criteria: How we measure success (testable)

    Constitutional Compliance:
        - Article V: Spec-driven development methodology
        - Law #2: Strict typing with Pydantic
        - Law #8: Focused, single-purpose model
    """

    title: str = Field(..., min_length=1, description="Specification title")
    goals: list[str] = Field(
        ..., min_length=1, description="Primary goals (what feature accomplishes)"
    )
    personas: list[str] = Field(
        ..., min_length=1, description="User personas (who uses this, their needs)"
    )
    success_criteria: list[str] = Field(
        ..., min_length=1, description="Success criteria (testable acceptance criteria)"
    )
    metadata: SpecMetadata = Field(
        default_factory=SpecMetadata, description="Additional metadata (priority, tags, etc.)"
    )

    @field_validator("goals", "personas", "success_criteria")
    @classmethod
    def validate_non_empty_list(cls, v: list[str]) -> list[str]:
        """Validate lists are non-empty."""
        if not v:
            raise ValueError("List cannot be empty")
        return v


class SpecGenerator:
    """
    LLM-powered specification generator with VectorStore learning.

    Architecture:
        1. Query VectorStore for similar spec patterns (Article IV)
        2. Inject high-confidence patterns (≥ 0.6) into prompt
        3. Use Planner agent for LLM-powered spec generation
        4. Return structured Spec model with spec-kit template

    Constitutional Compliance:
        - Article IV: VectorStore query BEFORE generation (mandatory)
        - Article V: Spec-kit methodology
        - Law #5: Result pattern for error handling
        - Law #8: Focused, single-purpose class

    Example:
        >>> context = create_agent_context()
        >>> generator = SpecGenerator(context=context)
        >>> intent = Intent(title="Dark Mode", description="Add dark mode toggle")
        >>> result = generator.generate(intent)
        >>> spec = result.unwrap()
    """

    def __init__(self, context: AgentContext) -> None:
        """
        Initialize SpecGenerator with AgentContext.

        Args:
            context: AgentContext for VectorStore access and memory
        """
        self.context = context
        self._planner_available = True  # Flag for Planner availability

    def generate(self, intent: SpecIntent) -> Result[Spec, str]:
        """
        Generate formal specification from user intent.

        Workflow:
            1. Query VectorStore for similar spec patterns (Article IV)
            2. Filter patterns by confidence (≥ 0.6)
            3. Inject patterns into LLM prompt
            4. Use Planner agent for spec generation
            5. Parse and validate spec-kit template sections
            6. Return structured Spec model

        Args:
            intent: User intent with title, description, priority, tags

        Returns:
            Result[Spec, str]: Spec model on success, error message on failure

        Constitutional Compliance:
            - Article IV: MUST query VectorStore before generation
            - Article V: MUST follow spec-kit template
            - Law #5: Result pattern for error handling

        Example:
            >>> generator = SpecGenerator(context)
            >>> intent = SpecIntent(title="JWT Auth", description="Add JWT", tags=["auth"])
            >>> result = generator.generate(intent)
            >>> if result.is_ok():
            ...     spec = result.unwrap()
            ...     print(spec.goals)
        """
        try:
            # Step 1: Query VectorStore for patterns (Article IV - MANDATORY)
            patterns = self._query_vectorstore_patterns(intent)
            logger.info(
                f"Queried VectorStore: found {len(patterns)} patterns for intent '{intent.title}'"
            )

            # Step 2: Filter patterns by confidence threshold (≥ 0.6)
            # Note: Confidence may be in content field or top-level
            high_confidence_patterns = []
            for p in patterns:
                confidence = p.get("confidence", 0.0)
                # Check content field if confidence not at top level
                if confidence == 0.0 and "content" in p:
                    content = p["content"]
                    if isinstance(content, dict):
                        confidence = content.get("confidence", 0.0)

                if confidence >= 0.6:
                    high_confidence_patterns.append(p)

            logger.debug(
                f"High-confidence patterns: {len(high_confidence_patterns)}/{len(patterns)}"
            )

            # Step 3: Generate spec with Planner agent (LLM-powered)
            spec_result = self._generate_with_planner(intent, high_confidence_patterns)

            if spec_result.is_err():
                # Fallback to template-based generation
                logger.warning(
                    f"Planner generation failed: {spec_result.unwrap_err()}, "
                    "using template fallback"
                )
                return self._generate_with_template(intent, high_confidence_patterns)

            spec = spec_result.unwrap()

            # Store spec generation success in memory (Article IV)
            self.context.store_memory(
                f"spec_generated_{intent.title}",
                {
                    "intent": intent.model_dump(),
                    "spec_title": spec.title,
                    "goals_count": len(spec.goals),
                    "patterns_used": len(high_confidence_patterns),
                },
                ["spec", "generation", "success"],
            )

            return Ok(spec)

        except Exception as e:
            logger.error(f"Spec generation failed: {e}")
            return Err(f"spec_generation_error: {str(e)}")

    def _query_vectorstore_patterns(self, intent: SpecIntent) -> list[dict[str, Any]]:
        """
        Query VectorStore for similar spec patterns (Article IV).

        Searches for patterns matching intent tags and domain.
        Returns all matching patterns for confidence filtering.

        Args:
            intent: User intent with tags

        Returns:
            List of pattern dictionaries with confidence scores

        Constitutional Compliance:
            - Article IV: Mandatory VectorStore query before action
        """
        # Build search tags from intent
        search_tags = ["spec", "pattern"]
        search_tags.extend(intent.tags)

        # Search VectorStore (cross-session learning)
        patterns = self.context.search_memories(search_tags, include_session=False)

        # Also search with just ["spec", "pattern"] to catch generic patterns
        if not patterns and intent.tags:
            patterns = self.context.search_memories(["spec", "pattern"], include_session=False)
            # Filter by tag match in content
            patterns = [
                p
                for p in patterns
                if any(tag in str(p.get("content", {})).lower() for tag in intent.tags)
            ]

        return patterns

    def _generate_with_planner(
        self, intent: SpecIntent, patterns: list[dict[str, Any]]
    ) -> Result[Spec, str]:
        """
        Generate spec using Planner agent (LLM-powered).

        Constructs prompt with intent details and VectorStore patterns,
        spawns Planner agent for generation, parses response.

        Args:
            intent: User intent
            patterns: High-confidence patterns from VectorStore

        Returns:
            Result[Spec, str]: Spec on success, error on failure
        """
        if not self._planner_available:
            return Err("planner_unavailable")

        try:
            # Build prompt with intent and patterns
            prompt = self._build_planner_prompt(intent, patterns)

            # For now, use template-based generation (Planner integration deferred)
            # TODO: Spawn Planner agent with prompt for LLM-powered generation
            # planner_response = self._invoke_planner_agent(prompt)

            # Fallback to template for initial implementation
            return self._generate_with_template(intent, patterns)

        except Exception as e:
            logger.error(f"Planner generation failed: {e}")
            return Err(f"planner_error: {str(e)}")

    def _generate_with_template(
        self, intent: SpecIntent, patterns: list[dict[str, Any]]
    ) -> Result[Spec, str]:
        """
        Generate spec using spec-kit template (fallback/bootstrap).

        Creates spec with template structure, injects VectorStore patterns,
        ensures all required sections present.

        Args:
            intent: User intent
            patterns: High-confidence patterns from VectorStore

        Returns:
            Result[Spec, str]: Spec with spec-kit template structure

        Constitutional Compliance:
            - Article V: Spec-kit methodology (Goals, Personas, Success Criteria)
        """
        try:
            # Extract goals from patterns (may be in content field)
            pattern_goals = []
            for pattern in patterns:
                # Try direct access first
                if "goals" in pattern:
                    pattern_goals.extend(pattern["goals"])
                # Try content field
                elif "content" in pattern:
                    content = pattern["content"]
                    if isinstance(content, dict) and "goals" in content:
                        pattern_goals.extend(content["goals"])

            # Build Goals section
            goals = self._build_goals(intent, pattern_goals)

            # Build Personas section
            personas = self._build_personas(intent)

            # Build Success Criteria section
            success_criteria = self._build_success_criteria(intent)

            # Build metadata
            metadata = {
                "intent_priority": intent.priority,
                "intent_tags": intent.tags,
                "patterns_used": len(patterns),
            }

            # Create Spec model
            spec = Spec(
                title=intent.title,
                goals=goals,
                personas=personas,
                success_criteria=success_criteria,
                metadata=metadata,
            )

            return Ok(spec)

        except Exception as e:
            logger.error(f"Template generation failed: {e}")
            return Err(f"template_error: {str(e)}")

    def _build_planner_prompt(self, intent: SpecIntent, patterns: list[dict[str, Any]]) -> str:
        """
        Build prompt for Planner agent with intent and patterns.

        Constructs structured prompt following spec-kit template,
        includes VectorStore patterns for learning-informed generation.

        Args:
            intent: User intent
            patterns: High-confidence patterns

        Returns:
            Formatted prompt string
        """
        # Build pattern context
        pattern_context = "\n".join(
            [
                f"- Pattern: {p.get('pattern_type', 'unknown')}, "
                f"Domain: {p.get('domain', 'general')}, "
                f"Goals: {p.get('goals', [])}"
                for p in patterns
            ]
        )

        prompt = f"""
Generate formal specification following spec-kit methodology.

INTENT:
Title: {intent.title}
Description: {intent.description}
Priority: {intent.priority}
Tags: {", ".join(intent.tags)}

VECTORSTORE PATTERNS (confidence ≥ 0.6):
{pattern_context if pattern_context else "No patterns found"}

REQUIRED SECTIONS (spec-kit template):
1. Goals: What this feature WILL accomplish (specific, measurable)
2. Personas: Who uses this feature (role, goals, pain points)
3. Success Criteria: How we measure success (testable acceptance criteria)

Generate comprehensive specification with 2+ goals, 1+ personas, 3+ success criteria.
"""

        return prompt

    def _build_goals(self, intent: SpecIntent, pattern_goals: list[str]) -> list[str]:
        """
        Build Goals section with VectorStore pattern injection.

        Combines intent description with learned patterns for comprehensive goals.
        For complex intents, splits description into multiple goals.

        Args:
            intent: User intent
            pattern_goals: Goals extracted from VectorStore patterns

        Returns:
            List of goal strings
        """
        goals = []

        # Parse complex intent descriptions (comma-separated components)
        if "," in intent.description or ":" in intent.description:
            # Split by common separators and extract components
            components = []
            for sep in [",", ":"]:
                if sep in intent.description:
                    parts = intent.description.split(sep)
                    components.extend([p.strip() for p in parts if p.strip()])
                    break

            # Create goal for each component
            for component in components[1:]:  # Skip first (usually title restatement)
                if len(component) > 3:  # Filter noise
                    goals.append(f"{component.capitalize()}")
        else:
            # Single goal from description
            goals.append(f"Implement {intent.title}: {intent.description}")

        # Inject pattern goals (deduplicate and filter)
        for goal in pattern_goals:
            # Skip if already present (case-insensitive)
            if any(goal.lower() in g.lower() or g.lower() in goal.lower() for g in goals):
                continue
            goals.append(goal)

        # Add constitutional compliance goal
        goals.append("Ensure 100% test coverage and constitutional compliance (Articles I-V)")

        return goals

    def _build_personas(self, intent: SpecIntent) -> list[str]:
        """
        Build Personas section based on intent domain.

        Creates user personas based on feature tags and priority.

        Args:
            intent: User intent

        Returns:
            List of persona strings
        """
        personas = []

        # Domain-based personas
        if "auth" in intent.tags:
            personas.append(
                "API Consumer: Needs secure access to endpoints, wants transparent authentication"
            )
            personas.append(
                "Backend Developer: Needs to implement auth logic, wants clear security patterns"
            )
        elif "ui" in intent.tags:
            personas.append("End User: Needs intuitive UI, wants responsive design")
            personas.append("Frontend Developer: Needs component library, wants maintainable code")
        else:
            # Generic personas
            personas.append(
                f"Primary User: Needs {intent.title.lower()}, wants reliable functionality"
            )
            personas.append(
                "Developer: Needs to implement and maintain feature, wants clear specifications"
            )

        return personas

    def _build_success_criteria(self, intent: SpecIntent) -> list[str]:
        """
        Build Success Criteria section with testable acceptance criteria.

        Creates measurable criteria based on intent and constitutional requirements.

        Args:
            intent: User intent

        Returns:
            List of success criteria strings
        """
        criteria = [
            f"{intent.title} implemented and functional",
            "All tests pass (100% success rate, Article II)",
            "Code follows strict typing (no Dict[Any, Any], Law #2)",
            "Functions under 50 lines (Law #8)",
            "Result pattern for error handling (Law #5)",
        ]

        # Priority-based criteria
        if intent.priority in ["high", "critical"]:
            criteria.append("Performance validated with benchmarks")
            criteria.append("Security audit completed")

        return criteria


__all__ = ["SpecGenerator", "SpecIntent", "Spec"]
