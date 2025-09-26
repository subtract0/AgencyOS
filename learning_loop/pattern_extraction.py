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

import re
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from shared.type_definitions.json import JSONValue
from dataclasses import dataclass, asdict
from pathlib import Path

from core.patterns import UnifiedPatternStore, get_pattern_store, Pattern as ExistingPattern
from core.telemetry import get_telemetry, emit


@dataclass
class Trigger:
    """Base class for pattern triggers."""
    type: str
    metadata: Dict[str, JSONValue]

    def to_dict(self) -> Dict[str, JSONValue]:
        """Convert trigger to dictionary for serialization."""
        return {
            "type": self.type,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, JSONValue]) -> "Trigger":
        """Create trigger from dictionary."""
        return cls(
            type=data["type"],
            metadata=data["metadata"]
        )


@dataclass
class ErrorTrigger(Trigger):
    """Trigger based on specific error patterns."""
    error_type: str
    error_pattern: str

    def __init__(self, error_type: str, error_pattern: str):
        self.error_type = error_type
        self.error_pattern = error_pattern
        super().__init__(
            type="error",
            metadata={
                "error_type": error_type,
                "error_pattern": error_pattern
            }
        )


@dataclass
class TaskTrigger(Trigger):
    """Trigger based on task description keywords."""
    keywords: List[str]

    def __init__(self, keywords: List[str]):
        self.keywords = keywords
        super().__init__(
            type="task",
            metadata={
                "keywords": keywords
            }
        )


@dataclass
class Condition:
    """Represents a precondition or postcondition."""
    type: str  # "file_exists", "test_passes", "error_absent", etc.
    target: str  # file path, test name, etc.
    value: Any  # expected value or condition details
    operator: str = "equals"  # "equals", "contains", "matches", etc.

    def evaluate(self, context: Dict[str, JSONValue]) -> bool:
        """Evaluate this condition against a context."""
        if self.type == "file_exists":
            return Path(self.target).exists()
        elif self.type == "test_passes":
            # This would need integration with test runner
            return context.get("tests_passing", False)
        elif self.type == "error_absent":
            return self.target not in context.get("errors", [])
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
    parameters: Dict[str, JSONValue]
    output_pattern: Optional[str] = None
    timeout_seconds: Optional[int] = None

    def to_dict(self) -> Dict[str, JSONValue]:
        """Convert action to dictionary for serialization."""
        return {
            "tool": self.tool,
            "parameters": self.parameters,
            "output_pattern": self.output_pattern,
            "timeout_seconds": self.timeout_seconds
        }

    @classmethod
    def from_dict(cls, data: Dict[str, JSONValue]) -> "Action":
        """Create action from dictionary."""
        return cls(
            tool=data["tool"],
            parameters=data["parameters"],
            output_pattern=data.get("output_pattern"),
            timeout_seconds=data.get("timeout_seconds")
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
    tags: List[str]

    def to_dict(self) -> Dict[str, JSONValue]:
        """Convert metadata to dictionary."""
        return {
            "confidence": self.confidence,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_used": self.last_used.isoformat(),
            "created_at": self.created_at.isoformat(),
            "source": self.source,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, JSONValue]) -> "PatternMetadata":
        """Create metadata from dictionary."""
        return cls(
            confidence=data["confidence"],
            usage_count=data["usage_count"],
            success_count=data["success_count"],
            failure_count=data["failure_count"],
            last_used=datetime.fromisoformat(data["last_used"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            source=data["source"],
            tags=data["tags"]
        )


@dataclass
class EnhancedPattern:
    """Enhanced pattern structure per SPEC-LEARNING-001."""
    id: str
    trigger: Trigger
    preconditions: List[Condition]
    actions: List[Action]
    postconditions: List[Condition]
    metadata: PatternMetadata

    def to_existing_pattern(self) -> ExistingPattern:
        """Convert to existing UnifiedPatternStore Pattern format."""
        return ExistingPattern(
            id=self.id,
            pattern_type=self.trigger.type,
            context={
                "trigger": self.trigger.to_dict(),
                "preconditions": [asdict(pc) for pc in self.preconditions],
                "postconditions": [asdict(pc) for pc in self.postconditions]
            },
            solution=json.dumps([action.to_dict() for action in self.actions]),
            success_rate=self.metadata.confidence,
            usage_count=self.metadata.usage_count,
            created_at=self.metadata.created_at.isoformat(),
            last_used=self.metadata.last_used.isoformat(),
            tags=self.metadata.tags
        )

    @classmethod
    def from_existing_pattern(cls, pattern: ExistingPattern) -> "EnhancedPattern":
        """Create from existing UnifiedPatternStore Pattern format."""
        context = pattern.context

        # Reconstruct trigger
        trigger_data = context.get("trigger", {})
        if trigger_data.get("type") == "error":
            trigger = ErrorTrigger(
                error_type=trigger_data.get("metadata", {}).get("error_type", ""),
                error_pattern=trigger_data.get("metadata", {}).get("error_pattern", "")
            )
        else:
            trigger = TaskTrigger(
                keywords=trigger_data.get("metadata", {}).get("keywords", [])
            )

        # Reconstruct conditions
        preconditions = [
            Condition(**pc_data) for pc_data in context.get("preconditions", [])
        ]
        postconditions = [
            Condition(**pc_data) for pc_data in context.get("postconditions", [])
        ]

        # Reconstruct actions
        try:
            actions_data = json.loads(pattern.solution)
            actions = [Action.from_dict(action_data) for action_data in actions_data]
        except (json.JSONDecodeError, TypeError):
            # Fallback for legacy patterns
            actions = []

        # Reconstruct metadata
        metadata = PatternMetadata(
            confidence=pattern.success_rate,
            usage_count=pattern.usage_count,
            success_count=int(pattern.success_rate * pattern.usage_count),
            failure_count=pattern.usage_count - int(pattern.success_rate * pattern.usage_count),
            last_used=datetime.fromisoformat(pattern.last_used),
            created_at=datetime.fromisoformat(pattern.created_at),
            source="learned",
            tags=pattern.tags
        )

        return cls(
            id=pattern.id,
            trigger=trigger,
            preconditions=preconditions,
            actions=actions,
            postconditions=postconditions,
            metadata=metadata
        )


@dataclass
class Operation:
    """Represents an operation that can be learned from."""
    id: str
    task_description: Optional[str]
    initial_error: Optional[Dict[str, JSONValue]]
    tool_calls: List[Dict[str, JSONValue]]
    final_state: Dict[str, JSONValue]
    success: bool
    duration_seconds: float
    timestamp: datetime

    @property
    def caused_regression(self) -> bool:
        """Check if operation caused a regression."""
        return self.final_state.get("test_results", {}).get("regressions", 0) > 0


@dataclass
class FailureReason:
    """Base class for failure analysis."""
    type: str
    description: str
    details: Dict[str, JSONValue]


class TestFailureAnalysis(FailureReason):
    """Failure due to test failures."""

    def __init__(self, failed_tests: List[str], root_cause: str):
        self.failed_tests = failed_tests
        self.root_cause = root_cause
        super().__init__(
            type="test_failure",
            description=f"Tests failed: {', '.join(failed_tests[:3])}",
            details={
                "failed_tests": failed_tests,
                "root_cause": root_cause
            }
        )


class ExecutionError(FailureReason):
    """Failure due to execution errors."""

    def __init__(self, error_type: str, error_message: str):
        self.error_type = error_type
        self.error_message = error_message
        super().__init__(
            type="execution_error",
            description=f"{error_type}: {error_message}",
            details={
                "error_type": error_type,
                "error_message": error_message
            }
        )


@dataclass
class AntiPattern:
    """Represents a learned anti-pattern from failures."""
    id: str
    trigger: Trigger
    failed_approach: List[Action]
    failure_reason: FailureReason
    alternative_approaches: List[str]
    severity: str  # "low", "medium", "high"


class PatternExtractor:
    """
    Extracts reusable patterns from successful operations.

    Implements SPEC-LEARNING-001 Section 2.1: Success Pattern Extraction.
    """

    def __init__(self, pattern_store: Optional[UnifiedPatternStore] = None):
        """
        Initialize pattern extractor.

        Args:
            pattern_store: Pattern storage instance (defaults to global store)
        """
        self.pattern_store = pattern_store or get_pattern_store()
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
            tags=self._generate_tags(operation, trigger)
        )

        pattern = EnhancedPattern(
            id=pattern_id,
            trigger=trigger,
            preconditions=preconditions,
            actions=actions,
            postconditions=postconditions,
            metadata=metadata
        )

        # Store in pattern store
        existing_pattern = pattern.to_existing_pattern()
        self.pattern_store.add(existing_pattern)

        # Emit telemetry
        emit("pattern_extracted", {
            "pattern_id": pattern_id,
            "trigger_type": trigger.type,
            "action_count": len(actions),
            "confidence": metadata.confidence
        })

        return pattern

    def _identify_trigger(self, operation: Operation) -> Trigger:
        """Identify what triggered this operation."""
        if operation.initial_error:
            error_type = operation.initial_error.get("type", "Unknown")
            error_message = operation.initial_error.get("message", "")

            # Extract error pattern using regex
            if "AttributeError" in error_message and "NoneType" in error_message:
                error_pattern = r"AttributeError.*'NoneType'.*has no attribute.*"
            elif "ImportError" in error_message or "ModuleNotFoundError" in error_message:
                error_pattern = r"(?:ImportError|ModuleNotFoundError).*"
            elif "SyntaxError" in error_message:
                error_pattern = r"SyntaxError.*line\s+\d+"
            else:
                error_pattern = f"{error_type}.*"

            return ErrorTrigger(
                error_type=error_type,
                error_pattern=error_pattern
            )

        elif operation.task_description:
            keywords = self._extract_keywords(operation.task_description)
            return TaskTrigger(keywords=keywords)

        else:
            # Default trigger
            return TaskTrigger(keywords=["general"])

    def _extract_keywords(self, text: str) -> List[str]:
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
        action_keywords = ["fix", "add", "remove", "update", "create", "delete", "modify", "refactor"]
        for keyword in action_keywords:
            if keyword in text_lower:
                keywords.append(keyword)

        # File type keywords
        file_keywords = ["test", "import", "function", "class", "method", "variable"]
        for keyword in file_keywords:
            if keyword in text_lower:
                keywords.append(keyword)

        return keywords if keywords else ["general"]

    def _extract_preconditions(self, operation: Operation) -> List[Condition]:
        """Extract preconditions that must be true before applying pattern."""
        conditions = []

        # If there was an error, add condition to check for its presence
        if operation.initial_error:
            error_type = operation.initial_error.get("type", "")
            conditions.append(Condition(
                type="error_present",
                target="current_error_type",
                value=error_type,
                operator="equals"
            ))

        # Extract file existence preconditions from tool calls
        for tool_call in operation.tool_calls:
            if tool_call.get("tool") == "Read":
                file_path = tool_call.get("parameters", {}).get("file_path")
                if file_path:
                    conditions.append(Condition(
                        type="file_exists",
                        target=file_path,
                        value=True,
                        operator="equals"
                    ))

        return conditions

    def _extract_action_sequence(self, operation: Operation) -> List[Action]:
        """Extract the sequence of actions that led to success."""
        actions = []

        for tool_call in operation.tool_calls:
            tool_name = tool_call.get("tool", "unknown")
            parameters = tool_call.get("parameters", {})
            output = tool_call.get("output", "")

            # Generalize parameters to make pattern reusable
            generalized_params = self._generalize_parameters(parameters)

            # Extract output pattern for validation
            output_pattern = self._extract_output_pattern(output) if output else None

            action = Action(
                tool=tool_name,
                parameters=generalized_params,
                output_pattern=output_pattern,
                timeout_seconds=tool_call.get("timeout", None)
            )

            actions.append(action)

        return actions

    def _generalize_parameters(self, parameters: Dict[str, JSONValue]) -> Dict[str, JSONValue]:
        """Generalize parameters to make them reusable."""
        generalized = {}

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

    def _extract_output_pattern(self, output: str) -> Optional[str]:
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
            (r"✓|✅|\bSUCCESS\b|\bPASS\b|\bOK\b", "success_indicator")
        ]

        for pattern, pattern_type in success_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return pattern

        return None

    def _extract_postconditions(self, operation: Operation) -> List[Condition]:
        """Extract postconditions that should be true after applying pattern."""
        conditions = []

        # Success condition
        conditions.append(Condition(
            type="operation_success",
            target="result",
            value=True,
            operator="equals"
        ))

        # Test passing condition if tests were involved (check both tool names and command content)
        test_involved = (
            any("test" in tool_call.get("tool", "").lower() for tool_call in operation.tool_calls) or
            any("pytest" in str(tool_call.get("parameters", {})).lower() for tool_call in operation.tool_calls)
        )

        if test_involved:
            conditions.append(Condition(
                type="test_passes",
                target="test_results",
                value=True,
                operator="equals"
            ))

        # Error absence condition if we started with an error
        if operation.initial_error:
            error_type = operation.initial_error.get("type", "")
            conditions.append(Condition(
                type="error_absent",
                target="errors",
                value=error_type,
                operator="not_contains"
            ))

        return conditions

    def _generate_tags(self, operation: Operation, trigger: Trigger) -> List[str]:
        """Generate tags for pattern categorization."""
        tags = ["auto_learned", "pattern_extraction"]

        # Add trigger-based tags
        tags.append(trigger.type)
        if hasattr(trigger, 'error_type'):
            tags.append(f"error_{trigger.error_type.lower()}")
        elif hasattr(trigger, 'keywords'):
            tags.extend(trigger.keywords)

        # Add tool-based tags
        tools_used = {tool_call.get("tool", "") for tool_call in operation.tool_calls}
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

    def __init__(self, pattern_store: Optional[UnifiedPatternStore] = None):
        """
        Initialize failure learner.

        Args:
            pattern_store: Pattern storage instance (defaults to global store)
        """
        self.pattern_store = pattern_store or get_pattern_store()
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
            severity=severity
        )

        # Store as negative pattern in pattern store
        negative_pattern = ExistingPattern(
            id=antipattern_id,
            pattern_type="anti_pattern",
            context={
                "trigger": trigger.to_dict(),
                "failed_approach": [action.to_dict() for action in failed_approach],
                "failure_reason": asdict(failure_reason),
                "severity": severity
            },
            solution=json.dumps(alternatives),
            success_rate=0.0,  # Anti-patterns have 0 success rate
            usage_count=0,
            created_at=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            tags=self._generate_failure_tags(operation, failure_reason)
        )

        self.pattern_store.add(negative_pattern)

        # Emit telemetry
        emit("antipattern_learned", {
            "antipattern_id": antipattern_id,
            "trigger_type": trigger.type,
            "failure_type": failure_reason.type,
            "severity": severity
        })

        return antipattern

    def _identify_trigger(self, operation: Operation) -> Trigger:
        """Identify what triggered this failed operation."""
        # Reuse the same logic as PatternExtractor
        extractor = PatternExtractor(self.pattern_store)
        return extractor._identify_trigger(operation)

    def _extract_failed_actions(self, operation: Operation) -> List[Action]:
        """Extract the sequence of actions that led to failure."""
        actions = []

        for tool_call in operation.tool_calls:
            action = Action(
                tool=tool_call.get("tool", "unknown"),
                parameters=tool_call.get("parameters", {}),
                output_pattern=None,  # Don't generalize for anti-patterns
                timeout_seconds=tool_call.get("timeout", None)
            )
            actions.append(action)

        return actions

    def _analyze_failure(self, operation: Operation) -> FailureReason:
        """Determine why the operation failed."""
        final_state = operation.final_state

        # Check for test failures
        test_results = final_state.get("test_results", {})
        if test_results and not test_results.get("passed", True):
            failed_tests = test_results.get("failures", [])
            root_cause = self._analyze_test_failures(test_results)

            return TestFailureAnalysis(
                failed_tests=failed_tests,
                root_cause=root_cause
            )

        # Check for execution errors
        error = final_state.get("error")
        if error:
            return ExecutionError(
                error_type=error.get("type", "Unknown"),
                error_message=error.get("message", "")
            )

        # Generic failure reason
        return FailureReason(
            type="unknown_failure",
            description="Operation failed for unknown reasons",
            details=final_state
        )

    def _analyze_test_failures(self, test_results: Dict[str, JSONValue]) -> str:
        """Analyze test failures to determine root cause."""
        failures = test_results.get("failures", [])

        if not failures:
            return "Unknown test failure"

        # Look for common patterns in failure messages
        failure_text = " ".join(str(f) for f in failures).lower()

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

    def _suggest_alternatives(self, operation: Operation) -> List[str]:
        """Suggest alternative approaches that might work better."""
        alternatives = []

        failure_reason = self._analyze_failure(operation)

        if failure_reason.type == "test_failure":
            alternatives.extend([
                "Add comprehensive null checks before attribute access",
                "Validate input parameters at function entry",
                "Use defensive programming patterns",
                "Add proper error handling with try-catch blocks"
            ])
        elif failure_reason.type == "execution_error":
            alternatives.extend([
                "Check file permissions and accessibility",
                "Validate tool parameters before execution",
                "Use more robust error handling",
                "Add timeout and retry mechanisms"
            ])

        # Add tool-specific alternatives
        tools_used = {tool_call.get("tool", "") for tool_call in operation.tool_calls}

        if "Edit" in tools_used:
            alternatives.extend([
                "Use MultiEdit for multiple related changes",
                "Validate file content before editing",
                "Create backup before making changes"
            ])

        if "Bash" in tools_used:
            alternatives.extend([
                "Use background execution for long-running commands",
                "Add proper timeout handling",
                "Check command exit codes"
            ])

        return alternatives

    def _generate_failure_tags(self, operation: Operation, failure_reason: FailureReason) -> List[str]:
        """Generate tags for anti-pattern categorization."""
        tags = ["anti_pattern", "failure_learning", failure_reason.type]

        # Add operation-specific tags
        if operation.caused_regression:
            tags.append("regression")

        # Add tool-based tags
        tools_used = {tool_call.get("tool", "") for tool_call in operation.tool_calls}
        tags.extend([f"failed_with_{tool.lower()}" for tool in tools_used if tool])

        return tags