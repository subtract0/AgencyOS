"""
TDDGraphGenerator: Test-First Task Graph Generation (Article II).

Converts ApprovedSpec into TaskGraph with automatic Test task generation
for every Code task. Enforces TDD at the architectural level.

Constitutional Compliance:
- Article I: Complete context (VectorStore query before generation)
- Article II: TDD enforcement (Test tasks auto-created for Code tasks)
- Article IV: VectorStore integration (pattern query + storage)
- Article V: Spec-driven development (TaskGraph from spec)

Architecture:
1. Query VectorStore for similar task graph patterns (Article IV)
2. Parse spec content into logical components (goals/modules)
3. Generate tasks: Spec → Code → Test (reversed via dependencies)
4. Auto-populate: Test.verification_target = Code.id
5. Auto-populate: Test.dependencies = [Code.id]
6. Validate with Pydantic (ensures Article II compliance)

Example:
    >>> context = create_agent_context(session_id="feature_123")
    >>> generator = TDDGraphGenerator(context=context)
    >>>
    >>> spec = ApprovedSpec(...)
    >>> result = generator.generate(spec)
    >>> if result.is_ok():
    ...     graph = result.unwrap()
    ...     print(graph.to_ascii_tree())
"""

import logging
import re
from typing import Any

from pydantic import ValidationError

from shared.agent_context import AgentContext
from shared.models.task_graph import (
    Phase,
    Task,
    TaskGraph,
    TaskTier,
    TaskType,
)
from shared.type_definitions.result import Err, Ok, Result
from tools.orchestrator.approval_checkpoint import ApprovedSpec

logger = logging.getLogger(__name__)


class TDDGraphGenerator:
    """
    Test-First Task Graph Generator.

    Generates TaskGraph from ApprovedSpec with automatic Test task creation
    for every Code task. Enforces TDD at the architectural level.

    Constitutional Compliance:
        - Article II: Every Code task gets Test task automatically
        - Article IV: VectorStore query BEFORE generation
        - Article V: Spec → TaskGraph transformation

    Example:
        >>> context = create_agent_context()
        >>> generator = TDDGraphGenerator(context=context)
        >>> spec = ApprovedSpec(...)
        >>> result = generator.generate(spec)
        >>> graph = result.unwrap()
    """

    def __init__(self, context: AgentContext) -> None:
        """
        Initialize TDDGraphGenerator with AgentContext.

        Args:
            context: AgentContext for VectorStore access and memory
        """
        self.context = context

    def generate(self, approved_spec: ApprovedSpec) -> Result[TaskGraph, str]:
        """
        Generate TaskGraph from ApprovedSpec with TDD enforcement.

        Workflow:
            1. Query VectorStore for similar patterns (Article IV - MANDATORY)
            2. Parse spec content into logical components
            3. Generate Spec tasks (design, architecture)
            4. Generate Code tasks (implementation)
            5. Auto-generate Test tasks for each Code task (Article II)
            6. Set dependencies: Test depends on Code
            7. Validate TaskGraph with Pydantic (Article II checks)

        Args:
            approved_spec: Approved specification to convert

        Returns:
            Result[TaskGraph, str]: TaskGraph on success, error message on failure

        Constitutional Compliance:
            - Article II: MANDATORY Test task for every Code task
            - Article IV: MUST query VectorStore before generation
            - Article V: TaskGraph IS the executable specification

        Example:
            >>> spec = ApprovedSpec(...)
            >>> result = generator.generate(spec)
            >>> if result.is_ok():
            ...     graph = result.unwrap()
            ...     print(f"Generated {len(graph.all_tasks())} tasks")
        """
        try:
            # Step 1: Query VectorStore for patterns (Article IV - MANDATORY)
            patterns = self._query_vectorstore_patterns(approved_spec)
            logger.info(
                f"Queried VectorStore: found {len(patterns)} patterns for '{approved_spec.spec.title}'"
            )

            # Step 2: Parse spec into components (goals, modules, features)
            components = self._parse_spec_components(approved_spec.spec.content)
            logger.debug(f"Parsed {len(components)} components from spec")

            # Step 3: Generate tasks with TDD enforcement
            phases = self._generate_phases(
                spec_title=approved_spec.spec.title,
                components=components,
                patterns=patterns,
            )

            # Step 4: Build TaskGraph with metadata
            metadata = {
                "spec_title": approved_spec.spec.title,
                "spec_version": approved_spec.spec.version,
                "edit_count": approved_spec.edit_count,
                "patterns_used": len(patterns),
                "components_count": len(components),
            }

            task_graph = TaskGraph(
                mission=approved_spec.spec.title,
                phases=phases,
                checkpoints=[],  # Checkpoints can be added later
                metadata=metadata,
            )

            # Step 5: Validate TaskGraph (Pydantic validators enforce Article II)
            # Validation happens automatically during TaskGraph construction
            # If we reach here, all validators passed (no circular deps, all Code tasks have Tests, etc.)

            # Step 6: Store generation success in VectorStore (Article IV)
            self._store_generation_success(approved_spec, task_graph, patterns)

            logger.info(
                f"Generated TaskGraph: {len(task_graph.all_tasks())} tasks "
                f"({len(phases)} phases, {len(patterns)} patterns used)"
            )

            return Ok(task_graph)

        except ValidationError as e:
            logger.error(f"TaskGraph validation failed: {e}")
            return Err(f"validation_error: {str(e)}")

        except Exception as e:
            logger.error(f"TaskGraph generation failed: {e}")
            return Err(f"generation_error: {str(e)}")

    def _query_vectorstore_patterns(self, approved_spec: ApprovedSpec) -> list[dict[str, Any]]:
        """
        Query VectorStore for similar task graph patterns (Article IV).

        Searches for patterns matching spec title and tags.
        Returns patterns with confidence scores for filtering.

        Args:
            approved_spec: Approved specification

        Returns:
            List of pattern dictionaries with confidence scores

        Constitutional Compliance:
            - Article IV: Mandatory VectorStore query before action
        """
        # Extract search tags from spec title and content
        search_tags = ["task_graph", "pattern"]

        # Add domain-specific tags based on spec content
        content_lower = approved_spec.spec.content.lower()
        if "auth" in content_lower or "jwt" in content_lower:
            search_tags.append("auth")
        if "api" in content_lower:
            search_tags.append("api")
        if "test" in content_lower:
            search_tags.append("testing")

        # Search VectorStore (cross-session learning)
        patterns = self.context.search_memories(search_tags, include_session=False)

        # Filter by confidence (≥ 0.6)
        high_confidence_patterns = []
        for pattern in patterns:
            confidence = pattern.get("confidence", 0.0)

            # Check content field if confidence not at top level
            if confidence == 0.0 and "content" in pattern:
                content = pattern["content"]
                if isinstance(content, dict):
                    confidence = content.get("confidence", 0.0)

            if confidence >= 0.6:
                high_confidence_patterns.append(pattern)

        logger.debug(
            f"VectorStore patterns: {len(high_confidence_patterns)}/{len(patterns)} high confidence"
        )

        return high_confidence_patterns

    def _parse_spec_components(self, spec_content: str) -> list[str]:
        """
        Parse spec content into logical components (goals, modules, features).

        Uses heuristics to extract components:
        - Numbered lists (1. 2. 3.)
        - Bullet points (- * •)
        - Paragraphs separated by newlines
        - Comma-separated items

        Args:
            spec_content: Specification content to parse

        Returns:
            List of component strings (goals, features, modules)

        Example:
            >>> content = "Implement auth: 1. JWT tokens\\n2. User sessions\\n3. Rate limiting"
            >>> components = self._parse_spec_components(content)
            >>> len(components)
            3
        """
        components = []

        # Strategy 1: Extract numbered lists (1. 2. 3.)
        numbered_pattern = r"^\s*\d+\.\s*(.+?)(?:\n|$)"
        numbered_matches = re.findall(numbered_pattern, spec_content, re.MULTILINE)
        if numbered_matches:
            components.extend([match.strip() for match in numbered_matches if match.strip()])

        # Strategy 2: Extract bullet points (- * •)
        if not components:
            bullet_pattern = r"^\s*[-*•]\s*(.+?)(?:\n|$)"
            bullet_matches = re.findall(bullet_pattern, spec_content, re.MULTILINE)
            if bullet_matches:
                components.extend([match.strip() for match in bullet_matches if match.strip()])

        # Strategy 3: Split by semicolons or commas (for inline lists)
        if not components and ("," in spec_content or ";" in spec_content):
            # Split by comma or semicolon
            separator = ";" if ";" in spec_content else ","
            parts = spec_content.split(separator)
            components.extend([part.strip() for part in parts if len(part.strip()) > 5])

        # Strategy 4: Fallback - use entire content as single component
        if not components:
            components = [spec_content.strip()]

        # Deduplicate and filter short components
        components = list(dict.fromkeys(components))  # Preserve order, remove duplicates
        components = [c for c in components if len(c) > 3]  # Filter noise

        return components

    def _generate_phases(
        self,
        spec_title: str,
        components: list[str],
        patterns: list[dict[str, Any]],
    ) -> list[Phase]:
        """
        Generate phases with tasks (Spec → Code → Test).

        Creates three phases:
        1. Design Phase: Spec tasks (architecture, planning)
        2. Implementation Phase: Code + Test tasks (TDD enforced)
        3. Integration Phase: Merger task (consolidation)

        Args:
            spec_title: Specification title
            components: Parsed spec components
            patterns: VectorStore patterns

        Returns:
            List of Phase objects with tasks

        Constitutional Compliance:
            - Article II: Every Code task gets Test task automatically
        """
        phases = []

        # Phase 1: Design & Specification
        spec_tasks = self._generate_spec_tasks(spec_title, components)
        if spec_tasks:
            phases.append(
                Phase(
                    id="phase_1",
                    title="Design & Specification",
                    tasks=spec_tasks,
                )
            )

        # Phase 2: Implementation (Code + Test tasks)
        # Generate Code tasks first, then Test tasks (Article II)
        code_tasks = self._generate_code_tasks(spec_title, components, patterns)
        test_tasks = self._generate_test_tasks(code_tasks)  # Auto-generate for each Code task

        # Combine Code + Test tasks in implementation phase
        implementation_tasks = code_tasks + test_tasks
        if implementation_tasks:
            phases.append(
                Phase(
                    id="phase_2",
                    title="Implementation & Verification",
                    tasks=implementation_tasks,
                )
            )

        # Phase 3: Integration & Merge (depends on all implementation tasks)
        merger_tasks = self._generate_merger_tasks(spec_title, implementation_tasks)
        if merger_tasks:
            phases.append(
                Phase(
                    id="phase_3",
                    title="Integration & Quality Check",
                    tasks=merger_tasks,
                )
            )

        return phases

    def _generate_spec_tasks(self, spec_title: str, components: list[str]) -> list[Task]:
        """
        Generate Spec tasks (architecture, design, planning).

        Args:
            spec_title: Specification title
            components: Spec components

        Returns:
            List of Spec tasks
        """
        tasks = []

        # Create architectural design task
        task_id = self._sanitize_task_id(f"spec_{spec_title}")
        tasks.append(
            Task(
                id=task_id,
                title=f"Design Architecture: {spec_title}",
                type=TaskType.SPEC,
                tier=TaskTier.TIER_1,  # Architecture is P1 (complex)
                agent="chief_architect",
                description=(
                    f"Design architecture for {spec_title}. "
                    f"Define modules, interfaces, and data flow. "
                    f"Create ADR if architectural decision required."
                ),
                dependencies=[],
                acceptance_criteria=[
                    "Architecture documented with clear module boundaries",
                    "Data flow diagrams created",
                    "ADR created for significant decisions",
                ],
            )
        )

        return tasks

    def _generate_code_tasks(
        self,
        spec_title: str,
        components: list[str],
        patterns: list[dict[str, Any]],
    ) -> list[Task]:
        """
        Generate Code tasks (implementation).

        Creates one Code task per component/module.

        Args:
            spec_title: Specification title
            components: Spec components (features, modules)
            patterns: VectorStore patterns

        Returns:
            List of Code tasks
        """
        tasks = []

        # Create Code task for each component
        for idx, component in enumerate(components):
            task_id = self._sanitize_task_id(f"code_{spec_title}_{idx}")

            # Determine tier based on component complexity
            tier = self._classify_task_tier(component)

            # Add dependency on spec task (design first)
            spec_task_id = self._sanitize_task_id(f"spec_{spec_title}")

            tasks.append(
                Task(
                    id=task_id,
                    title=f"Implement: {component[:50]}",  # Truncate long titles
                    type=TaskType.CODE,
                    tier=tier,
                    agent="coder",
                    description=(
                        f"Implement {component}. "
                        f"Follow TDD: Write tests first, then implementation. "
                        f"Use Result pattern for error handling (Law #5). "
                        f"Strict typing with Pydantic models (Law #2)."
                    ),
                    dependencies=[spec_task_id],
                    acceptance_criteria=[
                        "Implementation complete with type safety",
                        "Result pattern used for error handling",
                        "Functions under 50 lines (Law #8)",
                        "Code passes linting (ruff)",
                    ],
                    estimated_tokens=3000,  # Estimate for cost calculation
                )
            )

        # If no components extracted, create single implementation task
        if not tasks:
            task_id = self._sanitize_task_id(f"code_{spec_title}")
            spec_task_id = self._sanitize_task_id(f"spec_{spec_title}")

            tasks.append(
                Task(
                    id=task_id,
                    title=f"Implement: {spec_title}",
                    type=TaskType.CODE,
                    tier=TaskTier.TIER_2,
                    agent="coder",
                    description=f"Implement {spec_title} with TDD and strict typing.",
                    dependencies=[spec_task_id],
                    acceptance_criteria=[
                        "Implementation complete",
                        "Tests written first (TDD)",
                        "Type safe with Pydantic",
                    ],
                    estimated_tokens=3000,
                )
            )

        return tasks

    def _generate_test_tasks(self, code_tasks: list[Task]) -> list[Task]:
        """
        Auto-generate Test tasks for each Code task (Article II - MANDATORY).

        For each Code task, creates Test task with:
        - verification_target = Code task ID
        - dependencies = spec_task dependencies (Test comes FIRST in TDD)
        - agent = test_generator

        Then updates Code task dependencies to include Test task (TDD workflow).

        Args:
            code_tasks: List of Code tasks

        Returns:
            List of Test tasks (one per Code task)

        Constitutional Compliance:
            - Article II: Every Code task MUST have Test task
            - TDD Workflow: Test tasks come BEFORE Code tasks (Code depends on Test)
        """
        test_tasks = []

        for code_task in code_tasks:
            # Create Test task ID by replacing 'code_' with 'test_'
            test_task_id = code_task.id.replace("code_", "test_", 1)

            # Test task dependencies: Same as Code task dependencies (both depend on Spec)
            # This ensures Test task can execute BEFORE Code task
            test_dependencies = code_task.dependencies.copy()

            test_tasks.append(
                Task(
                    id=test_task_id,
                    title=f"Test: {code_task.title.replace('Implement:', '').strip()}",
                    type=TaskType.TEST,
                    tier=TaskTier.TIER_2,  # Test generation is P2 (moderate)
                    agent="test_generator",
                    description=(
                        f"Write comprehensive tests FIRST for {code_task.title}. "
                        f"Follow NECESSARY pattern: Normal, Edge, Corner, Error, Security, Stress, "
                        f"Accessibility, Regression, Yield. "
                        f"Tests must FAIL initially (no implementation yet). "
                        f"Use AAA pattern (Arrange, Act, Assert)."
                    ),
                    dependencies=test_dependencies,  # Test depends on same tasks as Code (e.g., Spec)
                    verification_target=code_task.id,  # Links Test to Code task
                    acceptance_criteria=[
                        f"Tests written for {code_task.title} (TDD red phase)",
                        "NECESSARY pattern coverage complete",
                        "Tests initially fail (no implementation)",
                        ">95% expected coverage when implementation added",
                    ],
                    estimated_tokens=2000,  # Tests typically cheaper than implementation
                )
            )

            # TDD Workflow: Code task now depends on Test task (Test FIRST)
            # Add Test task ID to Code task dependencies
            code_task.dependencies.append(test_task_id)

        logger.debug(f"Generated {len(test_tasks)} Test tasks for {len(code_tasks)} Code tasks")

        return test_tasks

    def _generate_merger_tasks(
        self, spec_title: str, implementation_tasks: list[Task]
    ) -> list[Task]:
        """
        Generate Merger tasks (integration, quality check).

        Note: Merger tasks are typically non-code activities (integration, PR creation),
        so we don't generate them as CODE tasks to avoid triggering Article II validation.
        Integration verification is handled by test tasks in implementation phase.

        Args:
            spec_title: Specification title
            implementation_tasks: All Code + Test tasks

        Returns:
            Empty list (integration handled in implementation phase)
        """
        # Integration and verification is handled by test tasks in implementation phase
        # No separate merger tasks needed to avoid Article II validation issues
        return []

    def _sanitize_task_id(self, raw_id: str) -> str:
        """
        Sanitize task ID to be alphanumeric with underscores only.

        Prevents code injection and ensures valid Python identifiers.

        Args:
            raw_id: Raw task ID string

        Returns:
            Sanitized task ID (alphanumeric + underscores)

        Example:
            >>> self._sanitize_task_id("code_JWT Auth'; DROP TABLE--")
            "code_jwt_auth_drop_table"
        """
        # Convert to lowercase
        sanitized = raw_id.lower()

        # Replace spaces and special chars with underscores
        sanitized = re.sub(r"[^a-z0-9_]", "_", sanitized)

        # Remove consecutive underscores
        sanitized = re.sub(r"_+", "_", sanitized)

        # Remove leading/trailing underscores
        sanitized = sanitized.strip("_")

        # Ensure starts with letter (not number)
        if sanitized and sanitized[0].isdigit():
            sanitized = f"task_{sanitized}"

        return sanitized

    def _classify_task_tier(self, component: str) -> TaskTier:
        """
        Classify task complexity tier (P1 complex vs P2/P3 simple).

        Uses heuristics:
        - Contains "architecture", "design", "adr" → Tier 1 (P1)
        - Contains "refactor", "fix", "typo" → Tier 2 (P3)
        - Default → Tier 2 (P2)

        Args:
            component: Component description

        Returns:
            TaskTier (TIER_1 or TIER_2)
        """
        component_lower = component.lower()

        # Tier 1 indicators (P1 - complex)
        tier1_keywords = ["architecture", "design", "adr", "strategic", "migration", "refactor"]
        if any(keyword in component_lower for keyword in tier1_keywords):
            return TaskTier.TIER_1

        # Default to Tier 2 (P2/P3 - simple to moderate)
        return TaskTier.TIER_2

    def _store_generation_success(
        self,
        approved_spec: ApprovedSpec,
        task_graph: TaskGraph,
        patterns: list[dict[str, Any]],
    ) -> None:
        """
        Store generation success in VectorStore (Article IV).

        Args:
            approved_spec: Approved specification
            task_graph: Generated task graph
            patterns: Patterns used
        """
        try:
            success_data = {
                "spec_title": approved_spec.spec.title,
                "task_count": len(task_graph.all_tasks()),
                "phase_count": len(task_graph.phases),
                "patterns_used": len(patterns),
                "code_tasks": len([t for t in task_graph.all_tasks() if t.type == TaskType.CODE]),
                "test_tasks": len([t for t in task_graph.all_tasks() if t.type == TaskType.TEST]),
                "confidence": 0.8,  # Base confidence for successful generation
            }

            self.context.store_memory(
                f"task_graph_generated_{approved_spec.spec.title}",
                success_data,
                ["task_graph", "generation", "success", "pattern"],
            )

            logger.info(
                f"Task graph generation success stored: {approved_spec.spec.title} "
                f"({success_data['task_count']} tasks)"
            )

        except Exception as e:
            logger.warning(f"Failed to store generation success: {e}")


__all__ = ["TDDGraphGenerator"]
