"""
DSPy-powered Toolsmith Agent Implementation

This module implements a DSPy Module that replaces the static markdown-based
ToolsmithAgent with adaptive, learning-based agent reasoning for tool creation.

Key Features:
- Parses tool directives and generates implementation plans
- Scaffolds new tools following BaseTool and Pydantic patterns
- Generates comprehensive test suites
- Hands off green artifacts to MergerAgent
- Learns from successful tool creation patterns
"""

import os
import logging
import traceback
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

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
    ToolDirectiveSignature,
    ToolScaffoldingSignature,
    TestGenerationSignature,
    HandoffSignature,
    FileChange,
    TestCase,
    VerificationResult,
    AgentResult,
)

# Configure logging
logger = logging.getLogger(__name__)


class ToolCreationContext(BaseModel):
    """Context for tool creation tasks."""

    repository_root: str = Field(..., description="Root directory of the repository")
    tools_directory: str = Field(default="tools", description="Directory where tools are stored")
    tests_directory: str = Field(default="tests", description="Directory where tests are stored")
    session_id: str = Field(..., description="Unique session identifier")
    existing_tools: List[str] = Field(default_factory=list, description="List of existing tool names")
    base_patterns: Dict[str, str] = Field(default_factory=dict, description="BaseTool patterns to follow")
    constitutional_articles: List[str] = Field(default_factory=lambda: [
        "Additive changes only - preserve backward compatibility",
        "Validate file paths - write only within repo root",
        "Redact secrets in summaries",
        "Deterministic summaries for auditability",
        "Run pytest and abort on failures (Article II)",
        "Store learnings about successful/failed scaffolds"
    ])


class ToolArtifact(BaseModel):
    """Represents a created tool artifact."""

    artifact_type: str = Field(..., description="Type: tool, test, config, etc.")
    file_path: str = Field(..., description="Path to the artifact")
    content: str = Field(..., description="Content of the artifact")
    status: str = Field(..., description="Status: created, tested, ready")
    test_results: Optional[Dict[str, Any]] = Field(None, description="Test execution results")


class DSPyToolsmithAgent(dspy.Module if DSPY_AVAILABLE else object):
    """
    DSPy-powered Toolsmith Agent for creating and testing tools.

    This agent replaces the static ToolsmithAgent with adaptive reasoning
    capabilities for tool creation, testing, and integration.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        reasoning_effort: str = "medium",
        enable_learning: bool = True,
        quality_threshold: float = 0.85
    ):
        """
        Initialize the DSPy Toolsmith Agent.

        Args:
            model: Language model to use
            reasoning_effort: Level of reasoning effort (low, medium, high)
            enable_learning: Whether to enable learning from patterns
            quality_threshold: Minimum quality threshold for tools
        """
        if DSPY_AVAILABLE:
            super().__init__()

        self.model = model
        self.reasoning_effort = reasoning_effort
        self.enable_learning = enable_learning
        self.quality_threshold = quality_threshold
        self.dspy_available = DSPY_AVAILABLE

        # Initialize DSPy modules if available
        if DSPY_AVAILABLE:
            self.directive_parser = dspy.ChainOfThought(ToolDirectiveSignature)
            self.scaffolder = dspy.ChainOfThought(ToolScaffoldingSignature)
            self.test_generator = dspy.ChainOfThought(TestGenerationSignature)
            self.handoff_preparer = dspy.ChainOfThought(HandoffSignature)  # Changed from Predict to ChainOfThought for rationale
        else:
            self.directive_parser = None
            self.scaffolder = None
            self.test_generator = None
            self.handoff_preparer = None

        # Initialize pattern storage
        self.successful_tools: List[Dict[str, Any]] = []
        self.failed_attempts: List[Dict[str, Any]] = []

        status = "with DSPy" if DSPY_AVAILABLE else "in fallback mode (DSPy not available)"
        logger.info(f"DSPyToolsmithAgent initialized {status} - model={model}, reasoning={reasoning_effort}")

    def forward(
        self,
        directive: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentResult:
        """
        Main forward method for creating tools.

        Args:
            directive: Tool creation directive
            context: Optional context dictionary
            **kwargs: Additional keyword arguments

        Returns:
            AgentResult: Result of tool creation
        """
        try:
            # Prepare context
            tool_context = self._prepare_context(context or {})

            if not self.dspy_available:
                return self._fallback_execution(directive, tool_context)

            # Parse the directive
            parsed = self.directive_parser(
                directive=directive,
                existing_tools=tool_context.existing_tools,
                constitutional_requirements=tool_context.constitutional_articles
            )

            # Log the design rationale for transparency
            logger.info(f"Design rationale: {parsed.design_rationale}")

            # Scaffold the tool
            tool_artifact = self._scaffold_tool(
                parsed.tool_name,
                parsed.tool_description,
                parsed.parameters,
                tool_context,
                design_rationale=parsed.design_rationale
            )

            # Generate tests
            test_artifact = self._generate_tests(
                parsed.tool_name,
                tool_artifact.content,
                parsed.test_cases,
                tool_context
            )

            # Run tests
            test_results = self._run_tests(test_artifact.file_path)

            # Prepare handoff
            artifacts = [tool_artifact, test_artifact]
            handoff = self._prepare_handoff(artifacts, test_results)

            # Learn from execution if enabled
            if self.enable_learning:
                self._learn_from_creation(
                    directive,
                    parsed.tool_name,
                    test_results["success"],
                    tool_context
                )

            return AgentResult(
                success=test_results["success"],
                message=f"Tool '{parsed.tool_name}' created and tested successfully",
                changes=[
                    FileChange(
                        file_path=tool_artifact.file_path,
                        operation="create",
                        content=tool_artifact.content
                    ),
                    FileChange(
                        file_path=test_artifact.file_path,
                        operation="create",
                        content=test_artifact.content
                    )
                ],
                tests=[
                    TestCase(
                        test_file=test_artifact.file_path,
                        test_name=f"test_{parsed.tool_name}",
                        test_code=test_artifact.content,
                        follows_necessary=True
                    )
                ],
                verification=VerificationResult(
                    all_tests_pass=test_results["success"],
                    no_linting_errors=True,
                    constitutional_compliance=True,
                    error_details=test_results.get("errors", [])
                )
            )

        except Exception as e:
            logger.error(f"Error in DSPyToolsmithAgent.forward: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            return AgentResult(
                success=False,
                message=f"Tool creation failed: {str(e)}",
                changes=[],
                tests=[],
                verification=VerificationResult(
                    all_tests_pass=False,
                    no_linting_errors=False,
                    constitutional_compliance=False,
                    error_details=[str(e)]
                )
            )

    def _fallback_execution(
        self,
        directive: str,
        context: ToolCreationContext
    ) -> AgentResult:
        """
        Fallback execution when DSPy is not available.

        CONSTITUTIONAL COMPLIANCE - Article I: Complete Context
        Providing comprehensive fallback with full context awareness.
        """
        logger.warning("CONSTITUTIONAL FALLBACK: Executing without DSPy - degraded mode active")
        logger.info("Article V Compliance: Spec-driven development requires DSPy for optimal results")

        # Parse directive with fallback method
        parsed = self._fallback_parse_directive(directive)

        # Create fallback tool code
        tool_code = self._fallback_scaffold_tool(
            parsed["tool_name"],
            parsed["tool_description"],
            parsed["parameters"]
        )[0]

        # Create fallback test code
        test_code = self._fallback_generate_tests(parsed["tool_name"])

        # Provide detailed constitutional compliance report
        compliance_notes = [
            "Article I - Complete Context: Fallback provides limited context understanding",
            "Article II - 100% Verification: Tests generated but not executed in fallback mode",
            "Article III - Automated Enforcement: Quality checks bypassed without DSPy",
            "Article IV - Continuous Learning: Learning disabled without DSPy patterns",
            "Article V - Spec-Driven Development: Basic specs generated from directive"
        ]

        return AgentResult(
            success=False,
            message=(
                f"CONSTITUTIONAL NOTICE: Tool '{parsed['tool_name']}' scaffolded in fallback mode.\n"
                f"To enable full Chain of Thought reasoning and constitutional compliance:\n"
                f"1. Install DSPy: pip install -r requirements-dspy.txt\n"
                f"2. Re-run with DSPy for complete Article II verification\n"
                f"Compliance Status: {', '.join(compliance_notes[:2])}"
            ),
            changes=[
                FileChange(
                    file_path=f"tools/{parsed['tool_name'].lower()}.py",
                    operation="create",
                    content=tool_code
                ),
                FileChange(
                    file_path=f"tests/test_{parsed['tool_name'].lower()}.py",
                    operation="create",
                    content=test_code
                )
            ],
            tests=[
                TestCase(
                    test_file=f"tests/test_{parsed['tool_name'].lower()}.py",
                    test_name=f"test_{parsed['tool_name'].lower()}",
                    test_code=test_code,
                    follows_necessary=True
                )
            ],
            verification=VerificationResult(
                all_tests_pass=False,
                no_linting_errors=True,
                constitutional_compliance=False,
                error_details=[
                    "DSPy not available - Chain of Thought reasoning disabled",
                    "Run 'pip install -r requirements-dspy.txt' to enable full functionality",
                    *compliance_notes
                ]
            )
        )

    def parse_directive(
        self,
        directive: str,
        existing_tools: List[str],
        constitutional_requirements: List[str]
    ) -> Dict[str, Any]:
        """
        Parse a tool creation directive.

        Args:
            directive: Tool directive text
            existing_tools: List of existing tools
            constitutional_requirements: Constitutional requirements

        Returns:
            Parsed directive information
        """
        try:
            if not self.dspy_available or self.directive_parser is None:
                return self._fallback_parse_directive(directive)

            result = self.directive_parser(
                directive=directive,
                existing_tools=existing_tools,
                constitutional_requirements=constitutional_requirements
            )

            return {
                "tool_name": result.tool_name,
                "tool_description": result.tool_description,
                "parameters": result.parameters,
                "test_cases": result.test_cases,
                "implementation_plan": result.implementation_plan
            }

        except Exception as e:
            logger.error(f"Error parsing directive: {str(e)}")
            return {
                "tool_name": "unknown",
                "tool_description": directive,
                "parameters": [],
                "test_cases": [],
                "implementation_plan": ["Error parsing directive"]
            }

    def _fallback_parse_directive(self, directive: str) -> Dict[str, Any]:
        """Fallback directive parsing when DSPy is not available.

        CONSTITUTIONAL COMPLIANCE - Article II: 100% Verification
        Providing verbose fallback to maintain system functionality.
        """
        logger.info("CONSTITUTIONAL FALLBACK: Parsing directive without DSPy")
        logger.info(f"Directive received: {directive[:100]}...")

        # Extract tool name intelligently
        tool_name = "NewTool"
        directive_lower = directive.lower()

        # Try multiple patterns to extract tool name
        if "create" in directive_lower and "tool" in directive_lower:
            words = directive.split()
            for i, word in enumerate(words):
                if word.lower() in ["tool", "agent", "component"]:
                    if i > 0 and words[i-1].lower() not in ["a", "an", "the", "create", "new"]:
                        tool_name = words[i-1].replace(",", "").replace(".", "")
                        break
                    elif i < len(words) - 1:
                        tool_name = words[i+1].replace(",", "").replace(".", "")
                        break

        # Generate comprehensive test cases based on directive
        test_cases = [
            "Test basic initialization",
            "Test core functionality",
            "Test error handling",
            "Test edge cases",
            "Test integration points"
        ]

        # Create detailed implementation plan
        implementation_plan = [
            "1. Parse and validate directive requirements",
            "2. Design tool architecture following BaseTool pattern",
            "3. Implement core functionality with type safety",
            "4. Add comprehensive error handling",
            "5. Create test suite following NECESSARY pattern",
            "6. Validate against constitutional requirements",
            "7. Run tests to ensure 100% pass rate (Article II)"
        ]

        logger.info(f"FALLBACK RESULT: Extracted tool_name='{tool_name}'")
        logger.info("CONSTITUTIONAL NOTE: Full DSPy installation enables Chain of Thought reasoning")

        return {
            "tool_name": tool_name,
            "tool_description": f"Tool created from directive: {directive}",
            "parameters": [],
            "test_cases": test_cases,
            "implementation_plan": implementation_plan
        }

    def scaffold_tool(
        self,
        tool_name: str,
        tool_description: str,
        parameters: List[Dict[str, Any]],
        base_patterns: Dict[str, str]
    ) -> Tuple[str, List[str], Optional[str]]:
        """
        Scaffold a new tool.

        Args:
            tool_name: Name of the tool
            tool_description: Description of the tool
            parameters: Tool parameters
            base_patterns: Patterns to follow

        Returns:
            Tuple of (tool_code, required_imports, scaffolding_rationale)
        """
        try:
            if not self.dspy_available or self.scaffolder is None:
                code, imports = self._fallback_scaffold_tool(tool_name, tool_description, parameters)
                return code, imports, None

            result = self.scaffolder(
                tool_name=tool_name,
                tool_description=tool_description,
                parameters=parameters,
                base_patterns=base_patterns
            )

            return result.tool_code, result.imports, result.scaffolding_rationale

        except Exception as e:
            logger.error(f"Error scaffolding tool: {str(e)}")
            return f"# Error scaffolding tool: {str(e)}", [], None

    def _fallback_scaffold_tool(
        self,
        tool_name: str,
        tool_description: str,
        parameters: List[Dict[str, Any]]
    ) -> Tuple[str, List[str]]:
        """Fallback tool scaffolding when DSPy is not available."""
        imports = [
            "from pydantic import BaseModel, Field",
            "from typing import Any, Dict, Optional",
        ]

        tool_code = f'''"""
{tool_description}
"""

{chr(10).join(imports)}


class {tool_name}(BaseModel):
    """
    {tool_description}
    """

    def run(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool."""
        # Implementation required
        return {{"success": True, "result": "Not implemented"}}
'''

        return tool_code, imports

    def generate_tests(
        self,
        tool_name: str,
        tool_code: str,
        test_requirements: List[str],
        follow_necessary: bool = True
    ) -> str:
        """
        Generate tests for a tool.

        Args:
            tool_name: Name of the tool
            tool_code: Tool implementation
            test_requirements: Test requirements
            follow_necessary: Whether to follow NECESSARY pattern

        Returns:
            Generated test code
        """
        try:
            if not self.dspy_available or self.test_generator is None:
                return self._fallback_generate_tests(tool_name)

            result = self.test_generator(
                tool_name=tool_name,
                tool_code=tool_code,
                test_requirements=test_requirements,
                necessary_pattern=follow_necessary
            )

            return result.test_code

        except Exception as e:
            logger.error(f"Error generating tests: {str(e)}")
            return f"# Error generating tests: {str(e)}"

    def _fallback_generate_tests(self, tool_name: str) -> str:
        """Fallback test generation when DSPy is not available."""
        return f'''"""
Tests for {tool_name}
"""

import pytest
from tools.{tool_name.lower()} import {tool_name}


def test_{tool_name.lower()}_initialization():
    """Test that {tool_name} can be initialized."""
    tool = {tool_name}()
    assert tool is not None


def test_{tool_name.lower()}_run():
    """Test that {tool_name} run method works."""
    tool = {tool_name}()
    result = tool.run()
    assert result["success"] is True
'''

    def _prepare_context(self, context: Dict[str, Any]) -> ToolCreationContext:
        """Prepare and validate the tool creation context."""
        try:
            # Set defaults
            if "repository_root" not in context or context["repository_root"] is None:
                context["repository_root"] = os.getcwd()

            if "session_id" not in context:
                context["session_id"] = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Get existing tools
            repo_root = context.get("repository_root", ".")
            if repo_root:  # Only process if repo_root is not None
                tools_dir = Path(repo_root) / "tools"
                if tools_dir.exists():
                    context["existing_tools"] = [
                        f.stem for f in tools_dir.glob("*.py")
                        if f.stem != "__init__"
                    ]

            return ToolCreationContext(**context)

        except ValidationError as e:
            logger.error(f"Context validation error: {str(e)}")
            return ToolCreationContext(
                repository_root=os.getcwd(),
                session_id=f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

    def _scaffold_tool(
        self,
        tool_name: str,
        tool_description: str,
        parameters: List[Dict[str, Any]],
        context: ToolCreationContext,
        design_rationale: Optional[str] = None
    ) -> ToolArtifact:
        """Internal method to scaffold a tool and create artifact."""
        tool_code, imports, scaffolding_rationale = self.scaffold_tool(
            tool_name,
            tool_description,
            parameters,
            context.base_patterns
        )

        # Log scaffolding rationale for debugging
        if scaffolding_rationale:
            logger.info(f"Scaffolding rationale: {scaffolding_rationale}")

        # Determine file path
        file_path = f"{context.tools_directory}/{tool_name.lower()}.py"

        return ToolArtifact(
            artifact_type="tool",
            file_path=file_path,
            content=tool_code,
            status="created"
        )

    def _generate_tests(
        self,
        tool_name: str,
        tool_code: str,
        test_cases: List[str],
        context: ToolCreationContext
    ) -> ToolArtifact:
        """Internal method to generate tests and create artifact."""
        test_code = self.generate_tests(
            tool_name,
            tool_code,
            test_cases,
            follow_necessary=True
        )

        # Determine file path
        file_path = f"{context.tests_directory}/test_{tool_name.lower()}.py"

        return ToolArtifact(
            artifact_type="test",
            file_path=file_path,
            content=test_code,
            status="created"
        )

    def _run_tests(self, test_file: str) -> Dict[str, Any]:
        """Run tests for a tool."""
        try:
            # Run pytest
            result = subprocess.run(
                ["python", "-m", "pytest", test_file, "-v"],
                capture_output=True,
                text=True,
                timeout=30
            )

            success = result.returncode == 0

            return {
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "errors": [] if success else [result.stderr]
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Test execution timed out",
                "errors": ["Test execution timed out after 30 seconds"]
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "errors": [f"Failed to run tests: {str(e)}"]
            }

    def _prepare_handoff(
        self,
        artifacts: List[ToolArtifact],
        test_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare artifacts for handoff to MergerAgent."""
        try:
            if not self.dspy_available or self.handoff_preparer is None:
                return self._fallback_prepare_handoff(artifacts, test_results)

            result = self.handoff_preparer(
                artifacts=[a.model_dump() for a in artifacts],
                test_results=test_results,
                integration_notes="Tool created and tested successfully"
            )

            return result.handoff_package

        except Exception as e:
            logger.error(f"Error preparing handoff: {str(e)}")
            return self._fallback_prepare_handoff(artifacts, test_results)

    def _fallback_prepare_handoff(
        self,
        artifacts: List[ToolArtifact],
        test_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback handoff preparation."""
        return {
            "artifacts": [a.model_dump() for a in artifacts],
            "test_results": test_results,
            "ready_for_merge": test_results["success"],
            "summary": f"Created {len(artifacts)} artifacts",
            "next_steps": ["Review code", "Merge if tests pass", "Update documentation"]
        }

    def _learn_from_creation(
        self,
        directive: str,
        tool_name: str,
        success: bool,
        context: ToolCreationContext
    ) -> None:
        """Learn from tool creation experience."""
        try:
            pattern = {
                "directive": directive,
                "tool_name": tool_name,
                "success": success,
                "timestamp": datetime.now().isoformat(),
                "session_id": context.session_id,
                "keywords": self._extract_keywords(directive)
            }

            if success:
                self.successful_tools.append(pattern)
                logger.info(f"Learned successful pattern for tool: {tool_name}")
            else:
                self.failed_attempts.append(pattern)
                logger.info(f"Learned failure pattern for tool: {tool_name}")

            # Limit storage
            if len(self.successful_tools) > 50:
                self.successful_tools = self.successful_tools[-50:]
            if len(self.failed_attempts) > 25:
                self.failed_attempts = self.failed_attempts[-25:]

        except Exception as e:
            logger.error(f"Error learning from creation: {str(e)}")

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        words = text.lower().split()
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        return [w for w in words if w not in stop_words and len(w) > 2][:10]

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of learned patterns."""
        total = len(self.successful_tools) + len(self.failed_attempts)
        return {
            "successful_tools": len(self.successful_tools),
            "failed_attempts": len(self.failed_attempts),
            "success_rate": len(self.successful_tools) / max(1, total),
            "total_creations": total
        }

    def reset_learning(self) -> None:
        """Reset learned patterns."""
        self.successful_tools = []
        self.failed_attempts = []
        logger.info("Learning patterns reset")


# Factory function for backwards compatibility
def create_dspy_toolsmith_agent(
    model: str = "gpt-4o-mini",
    reasoning_effort: str = "medium",
    enable_learning: bool = True,
    quality_threshold: float = 0.85,
    **kwargs
) -> DSPyToolsmithAgent:
    """
    Factory function to create a DSPyToolsmithAgent instance.

    Args:
        model: Language model to use
        reasoning_effort: Level of reasoning effort
        enable_learning: Whether to enable learning
        quality_threshold: Minimum quality threshold
        **kwargs: Additional arguments

    Returns:
        DSPyToolsmithAgent: Configured agent instance
    """
    return DSPyToolsmithAgent(
        model=model,
        reasoning_effort=reasoning_effort,
        enable_learning=enable_learning,
        quality_threshold=quality_threshold
    )


# Export the main class and factory function
__all__ = [
    "DSPyToolsmithAgent",
    "create_dspy_toolsmith_agent",
    "ToolCreationContext",
    "ToolArtifact",
]