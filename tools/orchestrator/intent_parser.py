"""
IntentParser - Parse user intent for two-stage TDD orchestration.

Constitutional compliance:
- Article I: Complete context (full parsing, no partial reads)
- Article II: Result pattern for error handling (no try/except control flow)
- Article IV: Memory Tool integration for backlog access

Reference: missions/leap_7_test_driven_autonomy.json task code_intent_parser
Author: AgencyOSAgent
Date: 2025-10-11
"""

import re
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from shared.agent_context import AgentContext
from shared.type_definitions.result import Err, Ok, Result


class InputMode(str, Enum):
    """
    Input mode for intent parsing.

    Modes:
        AUTO_SELECT: Auto-select highest priority Ready task from backlog
        NATURAL_LANGUAGE: Parse natural language intent string
        EXPLICIT_SPEC: Read from explicit spec file path
    """

    AUTO_SELECT = "auto_select"
    NATURAL_LANGUAGE = "natural_language"
    EXPLICIT_SPEC = "explicit_spec"


class Intent(BaseModel):
    """
    Parsed intent for TDD orchestration.

    Fields:
        description: Intent description text
        mode: Input mode used for parsing
        source: Source of intent (backlog path, spec file, or "natural_language")
        priority: Priority level (1=highest, default=2)
        tags: Intent categorization tags

    Constitutional Compliance:
        Article II: Strict typing (replaces dict[str, Any])
        Article IV: Structured intent data for VectorStore

    Example:
        >>> intent = Intent(
        ...     description="Implement JWT authentication",
        ...     mode=InputMode.NATURAL_LANGUAGE,
        ...     source="natural_language",
        ...     priority=1,
        ...     tags=["authentication", "security"]
        ... )
    """

    description: str = Field(
        ...,
        min_length=1,
        description="Intent description (non-empty)",
    )

    mode: InputMode = Field(
        ...,
        description="Input mode used for parsing",
    )

    source: str = Field(
        ...,
        min_length=1,
        description="Source of intent (backlog path, spec file, or 'natural_language')",
    )

    priority: int = Field(
        default=2,
        ge=1,
        le=3,
        description="Priority level (1=highest, 2=normal, 3=low)",
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Intent categorization tags",
    )


class IntentParser:
    """
    Parse user intent for two-stage TDD orchestration.

    Supports three input modes:
    1. AUTO_SELECT: Find highest priority Ready task from backlog
    2. NATURAL_LANGUAGE: Parse raw intent string
    3. EXPLICIT_SPEC: Read from spec file path

    Constitutional Compliance:
        Article I: Complete context (full file reads, no partial data)
        Article II: Result pattern for all operations
        Article IV: Memory Tool integration for backlog access

    Example:
        >>> parser = IntentParser(context)
        >>> result = parser.parse(None, InputMode.AUTO_SELECT)
        >>> if result.is_ok():
        ...     intent = result.unwrap()
        ...     print(f"Intent: {intent.description}")
    """

    def __init__(self, context: AgentContext):
        """
        Initialize intent parser.

        Args:
            context: AgentContext with Memory Tool access
        """
        self.context = context

    def parse(
        self,
        input_value: str | None,
        mode: InputMode,
    ) -> Result[Intent, str]:
        """
        Parse user intent based on mode.

        Args:
            input_value: Input string (None for AUTO_SELECT, intent for NATURAL_LANGUAGE, path for EXPLICIT_SPEC)
            mode: Input mode (AUTO_SELECT, NATURAL_LANGUAGE, EXPLICIT_SPEC)

        Returns:
            Result with Intent or error message

        Constitutional Compliance:
            Article I: Complete context before action (full reads)
            Article II: Result pattern (no exceptions for control flow)
            Article IV: Memory Tool integration
        """
        if mode == InputMode.AUTO_SELECT:
            return self._parse_auto_select()
        elif mode == InputMode.NATURAL_LANGUAGE:
            return self._parse_natural_language(input_value)
        elif mode == InputMode.EXPLICIT_SPEC:
            return self._parse_explicit_spec(input_value)
        else:
            return Err(f"Invalid input mode: {mode}")

    def _parse_auto_select(self) -> Result[Intent, str]:
        """
        Auto-select highest priority Ready task from backlog.

        Reads ~/.agency/memories/agency_backlog/test_suite_gaps.md
        and finds the first task marked [Ready].

        Returns:
            Result with Intent or error message

        Constitutional Compliance:
            Article I: Complete file read (no partial parsing)
            Article IV: Memory Tool integration
        """
        # Get Memory Tool from context
        memory_tool = self.context.get_anthropic_memory_tool()
        if memory_tool is None:
            return Err("Memory Tool not enabled. Call context.enable_anthropic_memory()")

        # Read backlog file
        backlog_path = "/memories/agency_backlog/test_suite_gaps.md"
        content = memory_tool.view(backlog_path)

        # Check for errors
        if content.startswith("Error:"):
            return Err(f"Failed to read backlog: {content}")

        # Parse backlog for [Ready] tasks
        lines = content.split("\n")
        current_task = None
        current_description = []

        for line in lines:
            # Match task header: ## Task: Description [Priority] [Status]
            task_match = re.match(
                r"^##\s+Task:\s+(.+?)\s+\[P(\d)\]\s+\[(Ready|Pending|In Progress|Done)\]",
                line,
            )
            if task_match:
                # If we found a Ready task, store it
                if current_task and current_task["status"] == "Ready":
                    return Ok(
                        Intent(
                            description=current_task["description"],
                            mode=InputMode.AUTO_SELECT,
                            source=backlog_path,
                            priority=current_task["priority"],
                            tags=["backlog", "auto_selected"],
                        )
                    )

                # Start new task
                current_task = {
                    "description": task_match.group(1).strip(),
                    "priority": int(task_match.group(2)),
                    "status": task_match.group(3),
                }
                current_description = []

        # Check final task
        if current_task and current_task["status"] == "Ready":
            return Ok(
                Intent(
                    description=current_task["description"],
                    mode=InputMode.AUTO_SELECT,
                    source=backlog_path,
                    priority=current_task["priority"],
                    tags=["backlog", "auto_selected"],
                )
            )

        # No Ready tasks found
        return Err("No Ready tasks found in backlog")

    def _parse_natural_language(
        self,
        input_value: str | None,
    ) -> Result[Intent, str]:
        """
        Parse natural language intent string.

        Args:
            input_value: Natural language intent description

        Returns:
            Result with Intent or error message

        Constitutional Compliance:
            Article II: Result pattern for validation errors
        """
        if not input_value:
            return Err("Natural language intent cannot be empty")

        if len(input_value.strip()) == 0:
            return Err("Natural language intent cannot be whitespace only")

        # Extract tags from intent (simple keyword extraction)
        tags = self._extract_tags(input_value)

        # Infer priority from keywords
        priority = self._infer_priority(input_value)

        return Ok(
            Intent(
                description=input_value.strip(),
                mode=InputMode.NATURAL_LANGUAGE,
                source="natural_language",
                priority=priority,
                tags=tags,
            )
        )

    def _parse_explicit_spec(
        self,
        input_value: str | None,
    ) -> Result[Intent, str]:
        """
        Read intent from explicit spec file.

        Args:
            input_value: Spec file path (absolute or relative)

        Returns:
            Result with Intent or error message

        Constitutional Compliance:
            Article I: Complete file read (no partial parsing)
            Article II: Result pattern for file errors
        """
        if not input_value:
            return Err("Spec file path cannot be empty")

        spec_path = Path(input_value).resolve()

        if not spec_path.exists():
            return Err(f"Spec file not found: {spec_path}")

        if not spec_path.is_file():
            return Err(f"Spec path is not a file: {spec_path}")

        # Read spec file (Article I: complete read)
        try:
            content = spec_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return Err(f"Spec file is not valid UTF-8: {spec_path}")
        except OSError as e:
            return Err(f"Failed to read spec file: {e}")

        if not content.strip():
            return Err("Spec file is empty")

        # Extract title from spec (look for # Title or ## Goals)
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            description = title_match.group(1).strip()
        else:
            # Fallback to first non-empty line
            for line in content.split("\n"):
                if line.strip() and not line.startswith("#"):
                    description = line.strip()
                    break
            else:
                description = f"Spec from {spec_path.name}"

        # Extract tags from spec content
        tags = self._extract_tags(content)
        tags.append("explicit_spec")

        return Ok(
            Intent(
                description=description,
                mode=InputMode.EXPLICIT_SPEC,
                source=str(spec_path),
                priority=1,  # Explicit specs are high priority
                tags=tags,
            )
        )

    def _extract_tags(self, text: str) -> list[str]:
        """
        Extract tags from text using keyword matching.

        Args:
            text: Text to extract tags from

        Returns:
            List of extracted tags
        """
        text_lower = text.lower()
        tags = []

        # Technical domain tags
        if any(kw in text_lower for kw in ["auth", "login", "jwt", "oauth"]):
            tags.append("authentication")
        if any(kw in text_lower for kw in ["test", "tdd", "coverage"]):
            tags.append("testing")
        if any(kw in text_lower for kw in ["api", "endpoint", "rest"]):
            tags.append("api")
        if any(kw in text_lower for kw in ["database", "db", "postgres", "sql"]):
            tags.append("database")
        if any(kw in text_lower for kw in ["refactor", "cleanup", "improve"]):
            tags.append("refactoring")
        if any(kw in text_lower for kw in ["bug", "fix", "error"]):
            tags.append("bugfix")
        if any(kw in text_lower for kw in ["feature", "implement", "add"]):
            tags.append("feature")
        if any(kw in text_lower for kw in ["security", "vulnerability", "exploit"]):
            tags.append("security")

        return tags

    def _infer_priority(self, text: str) -> int:
        """
        Infer priority from intent text.

        Args:
            text: Intent text

        Returns:
            Priority level (1=highest, 2=normal, 3=low)
        """
        text_lower = text.lower()

        # Priority 1: Critical/urgent/security keywords
        if any(
            kw in text_lower for kw in ["critical", "urgent", "security", "vulnerability", "broken"]
        ):
            return 1

        # Priority 3: Nice-to-have/cleanup/refactor keywords
        if any(kw in text_lower for kw in ["cleanup", "refactor", "nice to have", "optional"]):
            return 3

        # Default: Priority 2 (normal)
        return 2
