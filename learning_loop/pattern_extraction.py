"""
Pattern Extraction Logic: Learns patterns from successful operations and failures.

This module implements the core pattern extraction components specified in
SPEC-LEARNING-001 Section 2: Pattern Extraction Logic.

Constitutional Compliance:
- Article I: Complete context gathering before pattern extraction
- Article II: 100% test verification for all extracted patterns
- Article III: Automated pattern validation and quality enforcement
- Article IV: Continuous learning integration with VectorStore
- Article V: Spec-driven implementation following SPEC-LEARNING-001
"""

import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from core.telemetry import emit, get_telemetry
from pattern_intelligence import CodingPattern, PatternStore
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


def _safe_get_bool(data: JSONValue, key: str, default: bool = False) -> bool:
    """Safely extract bool from JSONValue dict with type checking."""
    if isinstance(data, dict) and key in data:
        value = data[key]
        if isinstance(value, bool):
            return value
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


@dataclass
class Trigger:
    """Base class for pattern triggers."""

    type: str
    metadata: dict[str, JSONValue]

    def to_dict(self) -> dict[str, JSONValue]:
        """Convert trigger to dictionary for serialization."""
        return {"type": self.type, "metadata": self.metadata}

    @classmethod
    def from_dict(cls, data: dict[str, JSONValue]) -> "Trigger":
        """Create trigger from dictionary."""
        return cls(type=_safe_get_str(data, "type"), metadata=_safe_get_dict(data, "metadata"))


@dataclass
class ErrorTrigger(Trigger):
    """Trigger based on specific error patterns."""

    error_type: str
    error_pattern: str

    def __init__(self, error_type: str, error_pattern: str):
        self.error_type = error_type
        self.error_pattern = error_pattern
        super().__init__(
            type="error", metadata={"error_type": error_type, "error_pattern": error_pattern}
        )


@dataclass
class TaskTrigger(Trigger):
    """Trigger based on task description keywords."""

    keywords: list[str]

    def __init__(self, keywords: list[str]):
        self.keywords = keywords
        super().__init__(type="task", metadata={"keywords": cast(JSONValue, keywords)})


@dataclass
class Condition:
    """Represents a precondition or postcondition."""

    type: str  # "file_exists", "test_passes", "error_absent", etc.
    target: str  # file path, test name, etc.
    value: Any  # expected value or condition details
    operator: str = "equals"  # "equals", "contains", "matches", etc.

    def evaluate(self, context: dict[str, JSONValue]) -> bool:
        """Evaluate this condition against a context."""
        if self.type == "file_exists":
            return Path(self.target).exists()
        elif self.type == "test_passes":
            # This would need integration with test runner
            tests_passing = context.get("tests_passing", False)
            return isinstance(tests_passing, bool) and tests_passing
        elif self.type == "error_absent":
            errors = context.get("errors", [])
            if isinstance(errors, list):
                return self.target not in [str(e) for e in errors]
            return True
        else:
            # Generic condition evaluation
            actual_value = context.get(self.target)
            if self.operator == "equals":
                return actual_value == self.value
            elif self.operator == "contains":
                return self.value in str(actual_value)
            elif self.operator == "matches":
                return bool(re.search(str(self.value), str(actual_value)))
            return False


@dataclass
class Action:
    """Represents a single action in a pattern."""

    tool: str
    parameters: dict[str, JSONValue]
    output_pattern: str | None = None
    timeout_seconds: int | None = None

    def to_dict(self) -> dict[str, JSONValue]:
        """Convert action to dictionary for serialization."""
        return {
            "tool": self.tool,
            "parameters": self.parameters,
            "output_pattern": self.output_pattern,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, JSONValue]) -> "Action":
        """Create action from dictionary."""
        return cls(
            tool=_safe_get_str(data, "tool"),
            parameters=_safe_get_dict(data, "parameters"),
            output_pattern=_safe_get_str(data, "output_pattern")
            if "output_pattern" in data
            else None,
            timeout_seconds=_safe_get_int(data, "timeout_seconds")
            if "timeout_seconds" in data
            else None,
        )


@dataclass
class PatternMetadata:
    """Enhanced metadata for patterns per spec."""

    confidence: float  # 0.0 to 1.0
    usage_count: int
    success_count: int
    failure_count: int
    last_used: datetime
    created_at: datetime
    source: str  # "learned", "manual", "imported"
    tags: list[str]

    def to_dict(self) -> dict[str, JSONValue]:
        """Convert metadata to dictionary."""
        return {
            "confidence": self.confidence,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_used": self.last_used.isoformat(),
            "created_at": self.created_at.isoformat(),
            "source": self.source,
            "tags": cast(JSONValue, self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict[str, JSONValue]) -> "PatternMetadata":
        """Create metadata from dictionary."""
        return cls(
            confidence=_safe_get_float(data, "confidence"),
            usage_count=_safe_get_int(data, "usage_count"),
            success_count=_safe_get_int(data, "success_count"),
            failure_count=_safe_get_int(data, "failure_count"),
            last_used=datetime.fromisoformat(_safe_get_str(data, "last_used")),
            created_at=datetime.fromisoformat(_safe_get_str(data, "created_at")),
            source=_safe_get_str(data, "source"),
            tags=_safe_get_list(data, "tags"),
        )


@dataclass
class EnhancedPattern:
    """Enhanced pattern structure per SPEC-LEARNING-001."""

    id: str
    trigger: Trigger
    preconditions: list[Condition]
    actions: list[Action]
    postconditions: list[Condition]
    metadata: PatternMetadata

    def to_coding_pattern(self) -> CodingPattern:
        """Convert to CodingPattern format."""
        from pattern_intelligence.coding_pattern import (
            EffectivenessMetric,
            ProblemContext,
            SolutionApproach,
        )
        from pattern_intelligence.coding_pattern import (
            PatternMetadata as CPMetadata,
        )

        # Get pattern representation based on trigger type
        trigger_pattern = self._get_trigger_pattern()

        # Build ProblemContext
        context = ProblemContext(
            description=trigger_pattern,
            domain=self.trigger.type,
            constraints=[self._condition_to_string(pc) for pc in self.preconditions],
            symptoms=[],
            scale=None,
            urgency="medium",
        )

        # Build SolutionApproach
        import json

        # Extract tools from actions
        tools_list = [
            action.tool for action in self.actions if hasattr(action, "tool") and action.tool
        ]
        solution = SolutionApproach(
            approach=f"Enhanced pattern for {self.trigger.type}",
            implementation=json.dumps([action.to_dict() for action in self.actions]),
            tools=tools_list if tools_list else ["generic"],  # Ensure at least one tool
            reasoning="Enhanced pattern extracted from learning loop",
            code_examples=[],
            dependencies=[],
            alternatives=[],
        )

        # Build EffectivenessMetric
        outcome = EffectivenessMetric(
            success_rate=self.metadata.confidence,
            performance_impact=None,
            maintainability_impact=None,
            user_impact=None,
            technical_debt=None,
            adoption_rate=self.metadata.usage_count,
            longevity=None,
            confidence=self.metadata.confidence,
        )

        # Build PatternMetadata
        metadata = CPMetadata(
            pattern_id=self.id,
            discovered_timestamp=self.metadata.created_at.isoformat(),
            source="learning_loop:pattern_extraction",
            discoverer="PatternExtractor",
            last_applied=self.metadata.last_used.isoformat() if self.metadata.last_used else None,
            application_count=self.metadata.usage_count,
            validation_status="validated",
            tags=self.metadata.tags,
            related_patterns=[],
        )

        return CodingPattern(context=context, solution=solution, outcome=outcome, metadata=metadata)

    def _get_trigger_pattern(self) -> str:
        """Get pattern representation based on trigger type."""
        if isinstance(self.trigger, ErrorTrigger):
            return self.trigger.error_pattern
        elif isinstance(self.trigger, TaskTrigger):
            return ", ".join(self.trigger.keywords)
        elif hasattr(self.trigger, "pattern"):
            return self.trigger.pattern  # type: ignore
        else:
            return str(self.trigger.metadata.get("pattern", ""))

    def _condition_to_string(self, condition: Condition) -> str:
        """Convert a Condition object to a string description."""
        return f"{condition.type}: {condition.target} {condition.operator} {condition.value}"

    @classmethod
    def from_coding_pattern(cls, pattern: CodingPattern) -> "EnhancedPattern":
        """Create from CodingPattern format."""
        # Simple conversion - create basic trigger from domain
        if pattern.context.domain == "error":
            trigger = ErrorTrigger(
                error_type=pattern.context.description, error_pattern=pattern.context.description
            )
        else:
            trigger = TaskTrigger(keywords=[pattern.context.domain])

        # Convert constraints to preconditions
        preconditions = []
        for constraint in pattern.context.constraints:
            preconditions.append(
                Condition(type="constraint", target="system", value=constraint, operator="equals")
            )

        # Convert postconditions (empty for now)
        postconditions = []

        # Reconstruct actions from implementation
        try:
            actions_data = json.loads(pattern.solution.implementation)
            actions = []
            if isinstance(actions_data, list):
                for action_data in actions_data:
                    if isinstance(action_data, dict):
                        actions.append(Action.from_dict(action_data))
        except (json.JSONDecodeError, TypeError):
            # Fallback - create a simple action
            actions = [
                Action(
                    type="implementation",
                    parameters={"approach": pattern.solution.approach},
                    description=pattern.solution.reasoning,
                )
            ]

        # Reconstruct metadata
        pattern_metadata = PatternMetadata(
            confidence=pattern.outcome.confidence or pattern.outcome.success_rate,
            usage_count=pattern.outcome.adoption_rate or 0,
            success_count=int(
                (pattern.outcome.confidence or pattern.outcome.success_rate)
                * (pattern.outcome.adoption_rate or 0)
            ),
            failure_count=(pattern.outcome.adoption_rate or 0)
            - int(
                (pattern.outcome.confidence or pattern.outcome.success_rate)
                * (pattern.outcome.adoption_rate or 0)
            ),
            last_used=datetime.fromisoformat(pattern.metadata.last_applied)
            if pattern.metadata.last_applied
            else datetime.fromisoformat(pattern.metadata.discovered_timestamp),
            created_at=datetime.fromisoformat(pattern.metadata.discovered_timestamp),
            source="pattern_intelligence",
            tags=pattern.metadata.tags,
        )

        return cls(
            id=pattern.metadata.pattern_id,
            trigger=trigger,
            preconditions=preconditions,
            actions=actions,
            postconditions=postconditions,
            metadata=pattern_metadata,
        )


@dataclass
class Operation:
    """Represents an operation that can be learned from."""

    id: str
    task_description: str | None
    initial_error: dict[str, JSONValue] | None
    tool_calls: list[dict[str, JSONValue]]
    final_state: dict[str, JSONValue]
    success: bool
    duration_seconds: float
    timestamp: datetime

    @property
    def caused_regression(self) -> bool:
        """Check if operation caused a regression."""
        test_results = self.final_state.get("test_results", {})
        if isinstance(test_results, dict):
            regressions = test_results.get("regressions", 0)
            if isinstance(regressions, (int, float)):
                return regressions > 0
        return False


@dataclass
class FailureReason:
    """Base class for failure analysis."""

    type: str
    description: str
    details: dict[str, JSONValue]


class FailureAnalysisWithTests(FailureReason):
    """Failure due to test failures."""

    def __init__(self, failed_tests: list[str], root_cause: str):
        self.failed_tests = failed_tests
        self.root_cause = root_cause
        super().__init__(
            type="test_failure",
            description=f"Tests failed: {', '.join(failed_tests[:3])}",
            details={"failed_tests": cast(JSONValue, failed_tests), "root_cause": root_cause},
        )


class ExecutionError(FailureReason):
    """Failure due to execution errors."""

    def __init__(self, error_type: str, error_message: str):
        self.error_type = error_type
        self.error_message = error_message
        super().__init__(
            type="execution_error",
            description=f"{error_type}: {error_message}",
            details={"error_type": error_type, "error_message": error_message},
        )


@dataclass
class AntiPattern:
    """Represents a learned anti-pattern from failures."""

    id: str
    trigger: Trigger
    failed_approach: list[Action]
    failure_reason: FailureReason
    alternative_approaches: list[str]
    severity: str  # "low", "medium", "high"


class PatternExtractor:
    """
    Extracts reusable patterns from successful operations.

    Implements SPEC-LEARNING-001 Section 2.1: Success Pattern Extraction.
    """

    def __init__(self, pattern_store: PatternStore | None = None):
        """
        Initialize pattern extractor.

        Args:
            pattern_store: Pattern storage instance (defaults to global store)
        """
        self.pattern_store = pattern_store or PatternStore()
        self.telemetry = get_telemetry()

    def extract_from_success(self, operation: Operation) -> EnhancedPattern:
        """
        Extract pattern from successful operation.

        Example operation:
        - Task: "Fix ImportError in test_agency.py"
        - Actions: [Read, Edit, Test]
        - Result: Tests passing

        Extracted pattern:
        - Trigger: "ImportError in test file"
        - Solution: "Add missing import statement"
        - Validation: "Run tests"

        Args:
            operation: Successful operation to learn from

        Returns:
            EnhancedPattern: Extracted reusable pattern
        """
        if not operation.success:
            raise ValueError("Cannot extract success pattern from failed operation")

        # Generate unique pattern ID
        pattern_id = f"success_{operation.id}_{uuid.uuid4().hex[:8]}"

        # Extract pattern components
        trigger = self._identify_trigger(operation)
        preconditions = self._extract_preconditions(operation)
        actions = self._extract_action_sequence(operation)
        postconditions = self._extract_postconditions(operation)

        # Create metadata with initial confidence
        metadata = PatternMetadata(
            confidence=0.5,  # Initial confidence per spec
            usage_count=0,
            success_count=0,
            failure_count=0,
            last_used=datetime.now(),
            created_at=datetime.now(),
            source="learned",
            tags=self._generate_tags(operation, trigger),
        )

        pattern = EnhancedPattern(
            id=pattern_id,
            trigger=trigger,
            preconditions=preconditions,
            actions=actions,
            postconditions=postconditions,
            metadata=metadata,
        )

        # Store in pattern store
        existing_pattern = pattern.to_coding_pattern()
        self.pattern_store.store_pattern(existing_pattern)

        # Emit telemetry
        emit(
            "pattern_extracted",
            {
                "pattern_id": pattern_id,
                "trigger_type": trigger.type,
                "action_count": len(actions),
                "confidence": metadata.confidence,
            },
        )

        return pattern

    def _identify_trigger(self, operation: Operation) -> Trigger:
        """Identify what triggered this operation."""
        if operation.initial_error:
            error_type = _safe_get_str(operation.initial_error, "type", "Unknown")
            error_message = _safe_get_str(operation.initial_error, "message", "")

            # Extract error pattern using regex
            if "AttributeError" in error_message and "NoneType" in error_message:
                error_pattern = r"AttributeError.*'NoneType'.*has no attribute.*"
            elif "ImportError" in error_message or "ModuleNotFoundError" in error_message:
                error_pattern = r"(?:ImportError|ModuleNotFoundError).*"
            elif "SyntaxError" in error_message:
                error_pattern = r"SyntaxError.*line\s+\d+"
            else:
                error_pattern = f"{error_type}.*"

            return ErrorTrigger(error_type=error_type, error_pattern=error_pattern)

        elif operation.task_description:
            keywords = self._extract_keywords(operation.task_description)
            return TaskTrigger(keywords=keywords)

        else:
            # Default trigger
            return TaskTrigger(keywords=["general"])

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract meaningful keywords from task description."""
        # Common programming keywords and patterns
        keywords = []
        text_lower = text.lower()

        # Error types
        error_keywords = ["error", "exception", "bug", "fail", "crash", "none", "null"]
        for keyword in error_keywords:
            if keyword in text_lower:
                keywords.append(keyword)

        # Action keywords
        action_keywords = [
            "fix",
            "add",
            "remove",
            "update",
            "create",
            "delete",
            "modify",
            "refactor",
        ]
        for keyword in action_keywords:
            if keyword in text_lower:
                keywords.append(keyword)

        # File type keywords
        file_keywords = ["test", "import", "function", "class", "method", "variable"]
        for keyword in file_keywords:
            if keyword in text_lower:
                keywords.append(keyword)

        return keywords if keywords else ["general"]

    def _extract_preconditions(self, operation: Operation) -> list[Condition]:
        """Extract preconditions that must be true before applying pattern."""
        conditions = []

        # If there was an error, add condition to check for its presence
        if operation.initial_error:
            error_type = _safe_get_str(operation.initial_error, "type")
            conditions.append(
                Condition(
                    type="error_present",
                    target="current_error_type",
                    value=error_type,
                    operator="equals",
                )
            )

        # Extract file existence preconditions from tool calls
        for tool_call in operation.tool_calls:
            tool_name = _safe_get_str(tool_call, "tool")
            if tool_name == "Read":
                parameters = _safe_get_dict(tool_call, "parameters")
                file_path = _safe_get_str(parameters, "file_path")
                if file_path:
                    conditions.append(
                        Condition(
                            type="file_exists", target=file_path, value=True, operator="equals"
                        )
                    )

        return conditions

    def _extract_action_sequence(self, operation: Operation) -> list[Action]:
        """Extract the sequence of actions that led to success."""
        actions = []

        for tool_call in operation.tool_calls:
            tool_name = _safe_get_str(tool_call, "tool", "unknown")
            parameters = _safe_get_dict(tool_call, "parameters")
            output = _safe_get_str(tool_call, "output")

            # Generalize parameters to make pattern reusable
            generalized_params = self._generalize_parameters(parameters)

            # Extract output pattern for validation
            output_pattern = self._extract_output_pattern(output) if output else None

            action = Action(
                tool=tool_name,
                parameters=generalized_params,
                output_pattern=output_pattern,
                timeout_seconds=_safe_get_int(tool_call, "timeout")
                if "timeout" in tool_call
                else None,
            )

            actions.append(action)

        return actions

    def _generalize_parameters(self, parameters: dict[str, JSONValue]) -> dict[str, JSONValue]:
        """Generalize parameters to make them reusable."""
        generalized: dict[str, JSONValue] = {}

        for key, value in parameters.items():
            if key == "file_path" and isinstance(value, str):
                # Generalize file paths
                if "test" in value:
                    generalized[key] = "{test_file}"
                elif ".py" in value:
                    generalized[key] = "{python_file}"
                else:
                    generalized[key] = "{file}"
            elif key in ["old_string", "new_string"] and isinstance(value, str):
                # Generalize code changes
                if "import" in value.lower():
                    generalized[key] = "{import_statement}"
                elif "def " in value:
                    generalized[key] = "{function_definition}"
                else:
                    generalized[key] = "{code_change}"
            elif key == "pattern" and isinstance(value, str):
                # Keep search patterns as-is but mark them as patterns
                generalized[key] = f"{{pattern: {value}}}"
            else:
                # Keep other parameters as-is
                generalized[key] = value

        return generalized

    def _extract_output_pattern(self, output: str) -> str | None:
        """Extract pattern from tool output for validation."""
        if not output:
            return None

        # Look for success indicators and return the most specific match
        # Order from most specific to least specific
        # Use word boundaries or more specific patterns to avoid false matches
        success_patterns = [
            (r"All tests passed", "all_tests_passed"),
            (r"File written successfully", "file_written"),
            (r"\d+ passed", "test_passed"),
            (r"✓|✅|\bSUCCESS\b|\bPASS\b|\bOK\b", "success_indicator"),
        ]

        for pattern, pattern_type in success_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return pattern

        return None

    def _extract_postconditions(self, operation: Operation) -> list[Condition]:
        """Extract postconditions that should be true after applying pattern."""
        conditions = []

        # Success condition
        conditions.append(
            Condition(type="operation_success", target="result", value=True, operator="equals")
        )

        # Test passing condition if tests were involved (check both tool names and command content)
        test_involved = any(
            "test" in _safe_get_str(tool_call, "tool").lower() for tool_call in operation.tool_calls
        ) or any(
            "pytest" in str(_safe_get_dict(tool_call, "parameters")).lower()
            for tool_call in operation.tool_calls
        )

        if test_involved:
            conditions.append(
                Condition(type="test_passes", target="test_results", value=True, operator="equals")
            )

        # Error absence condition if we started with an error
        if operation.initial_error:
            error_type = _safe_get_str(operation.initial_error, "type")
            conditions.append(
                Condition(
                    type="error_absent", target="errors", value=error_type, operator="not_contains"
                )
            )

        return conditions

    def _generate_tags(self, operation: Operation, trigger: Trigger) -> list[str]:
        """Generate tags for pattern categorization."""
        tags = ["auto_learned", "pattern_extraction"]

        # Add trigger-based tags
        tags.append(trigger.type)
        if hasattr(trigger, "error_type"):
            tags.append(f"error_{trigger.error_type.lower()}")
        elif hasattr(trigger, "keywords"):
            tags.extend(trigger.keywords)

        # Add tool-based tags
        tools_used = {_safe_get_str(tool_call, "tool") for tool_call in operation.tool_calls}
        tags.extend([f"uses_{tool.lower()}" for tool in tools_used if tool])

        # Add complexity tags
        if len(operation.tool_calls) > 5:
            tags.append("complex")
        elif len(operation.tool_calls) <= 2:
            tags.append("simple")
        else:
            tags.append("moderate")

        return list(set(tags))  # Remove duplicates


class FailureLearner:
    """
    Learns from failures to avoid repeating mistakes.

    Implements SPEC-LEARNING-001 Section 2.2: Failure Pattern Learning.
    """

    def __init__(self, pattern_store: PatternStore | None = None):
        """
        Initialize failure learner.

        Args:
            pattern_store: Pattern storage instance (defaults to global store)
        """
        self.pattern_store = pattern_store or PatternStore()
        self.telemetry = get_telemetry()

    def learn_from_failure(self, operation: Operation) -> AntiPattern:
        """
        Extract anti-pattern from failed operation.

        Args:
            operation: Failed operation to learn from

        Returns:
            AntiPattern: Learned anti-pattern to avoid
        """
        if operation.success:
            raise ValueError("Cannot extract failure pattern from successful operation")

        # Generate unique anti-pattern ID
        antipattern_id = f"failure_{operation.id}_{uuid.uuid4().hex[:8]}"

        # Extract components
        trigger = self._identify_trigger(operation)
        failed_approach = self._extract_failed_actions(operation)
        failure_reason = self._analyze_failure(operation)
        alternatives = self._suggest_alternatives(operation)
        severity = "high" if operation.caused_regression else "medium"

        antipattern = AntiPattern(
            id=antipattern_id,
            trigger=trigger,
            failed_approach=failed_approach,
            failure_reason=failure_reason,
            alternative_approaches=alternatives,
            severity=severity,
        )

        # Store as negative pattern in pattern store
        from pattern_intelligence.coding_pattern import (
            EffectivenessMetric,
            ProblemContext,
            SolutionApproach,
        )
        from pattern_intelligence.coding_pattern import (
            PatternMetadata as CPMetadata,
        )

        # Build anti-pattern as CodingPattern
        context = ProblemContext(
            description=f"Anti-pattern: {failure_reason.type}",
            domain="anti_pattern",
            constraints=[],
            symptoms=[str(failure_reason.details)],
            scale=None,
            urgency=severity,
        )

        solution = SolutionApproach(
            approach="Avoid this pattern",
            implementation=json.dumps(alternatives),
            tools=[],
            reasoning=f"Failed approach leads to: {failure_reason.details}",
            code_examples=[],
            dependencies=[],
            alternatives=alternatives,
        )

        outcome = EffectivenessMetric(
            success_rate=0.0,  # Anti-patterns have 0 success rate
            performance_impact="negative",
            maintainability_impact="negative",
            user_impact="negative",
            technical_debt="high",
            adoption_rate=0,
            longevity=None,
            confidence=1.0,  # High confidence it's bad
        )

        metadata = CPMetadata(
            pattern_id=antipattern_id,
            discovered_timestamp=datetime.now().isoformat(),
            source="learning_loop:anti_pattern",
            discoverer="FailureLearner",
            last_applied=None,
            application_count=0,
            validation_status="validated",
            tags=self._generate_failure_tags(operation, failure_reason),
            related_patterns=[],
        )

        negative_pattern = CodingPattern(
            context=context, solution=solution, outcome=outcome, metadata=metadata
        )

        self.pattern_store.store_pattern(negative_pattern)

        # Emit telemetry
        emit(
            "antipattern_learned",
            {
                "antipattern_id": antipattern_id,
                "trigger_type": trigger.type,
                "failure_type": failure_reason.type,
                "severity": severity,
            },
        )

        return antipattern

    def _identify_trigger(self, operation: Operation) -> Trigger:
        """Identify what triggered this failed operation."""
        # Reuse the same logic as PatternExtractor
        extractor = PatternExtractor(self.pattern_store)
        return extractor._identify_trigger(operation)

    def _extract_failed_actions(self, operation: Operation) -> list[Action]:
        """Extract the sequence of actions that led to failure."""
        actions = []

        for tool_call in operation.tool_calls:
            action = Action(
                tool=_safe_get_str(tool_call, "tool", "unknown"),
                parameters=_safe_get_dict(tool_call, "parameters"),
                output_pattern=None,  # Don't generalize for anti-patterns
                timeout_seconds=_safe_get_int(tool_call, "timeout")
                if "timeout" in tool_call
                else None,
            )
            actions.append(action)

        return actions

    def _analyze_failure(self, operation: Operation) -> FailureReason:
        """Determine why the operation failed."""
        final_state = operation.final_state

        # Check for test failures
        test_results = _safe_get_dict(final_state, "test_results")
        if test_results and not _safe_get_bool(test_results, "passed", True):
            failed_tests = _safe_get_list(test_results, "failures")
            root_cause = self._analyze_test_failures(test_results)

            return FailureAnalysisWithTests(failed_tests=failed_tests, root_cause=root_cause)

        # Check for execution errors
        error = _safe_get_dict(final_state, "error")
        if error:
            return ExecutionError(
                error_type=_safe_get_str(error, "type", "Unknown"),
                error_message=_safe_get_str(error, "message"),
            )

        # Generic failure reason
        return FailureReason(
            type="unknown_failure",
            description="Operation failed for unknown reasons",
            details=final_state,
        )

    def _analyze_test_failures(self, test_results: dict[str, JSONValue]) -> str:
        """Analyze test failures to determine root cause."""
        failures = _safe_get_list(test_results, "failures")

        if not failures:
            return "Unknown test failure"

        # Look for common patterns in failure messages
        failure_text = " ".join(failures).lower()

        if "assertion" in failure_text:
            return "Assertion failures - logic error in implementation"
        elif "import" in failure_text:
            return "Import errors - missing dependencies or circular imports"
        elif "syntax" in failure_text:
            return "Syntax errors - code formatting issues"
        elif "none" in failure_text or "null" in failure_text:
            return "NoneType errors - missing null checks"
        elif "timeout" in failure_text:
            return "Timeout errors - operation took too long"
        else:
            return f"Multiple test failures: {len(failures)} tests failed"

    def _suggest_alternatives(self, operation: Operation) -> list[str]:
        """Suggest alternative approaches that might work better."""
        alternatives = []

        failure_reason = self._analyze_failure(operation)

        if failure_reason.type == "test_failure":
            alternatives.extend(
                [
                    "Add comprehensive null checks before attribute access",
                    "Validate input parameters at function entry",
                    "Use defensive programming patterns",
                    "Add proper error handling with try-catch blocks",
                ]
            )
        elif failure_reason.type == "execution_error":
            alternatives.extend(
                [
                    "Check file permissions and accessibility",
                    "Validate tool parameters before execution",
                    "Use more robust error handling",
                    "Add timeout and retry mechanisms",
                ]
            )

        # Add tool-specific alternatives
        tools_used = {_safe_get_str(tool_call, "tool") for tool_call in operation.tool_calls}

        if "Edit" in tools_used:
            alternatives.extend(
                [
                    "Use MultiEdit for multiple related changes",
                    "Validate file content before editing",
                    "Create backup before making changes",
                ]
            )

        if "Bash" in tools_used:
            alternatives.extend(
                [
                    "Use background execution for long-running commands",
                    "Add proper timeout handling",
                    "Check command exit codes",
                ]
            )

        return alternatives

    def _generate_failure_tags(
        self, operation: Operation, failure_reason: FailureReason
    ) -> list[str]:
        """Generate tags for anti-pattern categorization."""
        tags = ["anti_pattern", "failure_learning", failure_reason.type]

        # Add operation-specific tags
        if operation.caused_regression:
            tags.append("regression")

        # Add tool-based tags
        tools_used = {_safe_get_str(tool_call, "tool") for tool_call in operation.tool_calls}
        tags.extend([f"failed_with_{tool.lower()}" for tool in tools_used if tool])

        return tags
