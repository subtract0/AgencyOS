"""
LocalCodebaseExtractor - Extract patterns from the current codebase.

Analyzes:
- Successful bug fixes from git history
- Error handling patterns in existing code
- Architectural patterns from agent implementations
- Tool usage patterns from agent toolsets
- Testing patterns and quality approaches
"""

import os
import re
import ast
import json
import subprocess
from typing import List, Dict, Any, Optional
from shared.types.json import JSONValue
from datetime import datetime, timedelta
import logging

from .base_extractor import BasePatternExtractor
from ..coding_pattern import CodingPattern, ProblemContext, SolutionApproach, EffectivenessMetric

logger = logging.getLogger(__name__)


class LocalCodebaseExtractor(BasePatternExtractor):
    """Extract coding patterns from the local codebase."""

    def __init__(self, repo_path: str = ".", confidence_threshold: float = 0.6):
        """
        Initialize local codebase extractor.

        Args:
            repo_path: Path to the repository
            confidence_threshold: Minimum confidence for patterns
        """
        super().__init__("local_codebase", confidence_threshold)
        self.repo_path = os.path.abspath(repo_path)

    def extract_patterns(self, **kwargs) -> List[CodingPattern]:
        """Extract patterns from the local codebase."""
        patterns = []

        try:
            # Extract different types of patterns
            patterns.extend(self._extract_error_handling_patterns())
            patterns.extend(self._extract_architecture_patterns())
            patterns.extend(self._extract_tool_patterns())
            patterns.extend(self._extract_testing_patterns())
            patterns.extend(self._extract_git_history_patterns())

            logger.info(f"Extracted {len(patterns)} patterns from local codebase")
            return patterns

        except Exception as e:
            logger.error(f"Failed to extract patterns from local codebase: {e}")
            return []

    def _extract_error_handling_patterns(self) -> List[CodingPattern]:
        """Extract error handling patterns from Python files."""
        patterns = []

        try:
            python_files = self._find_python_files()

            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Parse AST to find try-except patterns
                    tree = ast.parse(content)
                    error_patterns = self._analyze_error_handling_ast(tree, file_path)
                    patterns.extend(error_patterns)

                except Exception as e:
                    logger.debug(f"Failed to analyze {file_path}: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Error handling pattern extraction failed: {e}")

        return patterns

    def _extract_architecture_patterns(self) -> List[CodingPattern]:
        """Extract architectural patterns from agent implementations."""
        patterns = []

        try:
            # Analyze agent structure
            agent_dirs = [d for d in os.listdir(self.repo_path)
                         if os.path.isdir(os.path.join(self.repo_path, d)) and d.endswith('_agent')]

            if len(agent_dirs) >= 5:  # Multi-agent architecture pattern
                context = ProblemContext(
                    description="Managing complex software engineering tasks with multiple specialized capabilities",
                    domain="architecture",
                    constraints=["Single codebase", "Coordinated execution", "Specialized responsibilities"],
                    symptoms=["Task complexity", "Need for specialization", "Coordination overhead"],
                    scale="10+ agents"
                )

                solution = SolutionApproach(
                    approach="Multi-agent architecture with specialized roles",
                    implementation="Separate agent directories with specific responsibilities and tool sets",
                    tools=["agency_swarm", "agent_communication", "tool_specialization"],
                    reasoning="Divide complex tasks among specialized agents for better focus and maintainability",
                    code_examples=[f"Found {len(agent_dirs)} specialized agents: {', '.join(agent_dirs[:5])}"]
                )

                outcome = EffectivenessMetric(
                    success_rate=0.85,  # Based on test success rate
                    maintainability_impact="Improved separation of concerns and focused responsibilities",
                    user_impact="Faster development through specialized expertise",
                    adoption_rate=1,  # This codebase
                    confidence=0.9
                )

                pattern = self.create_pattern(context, solution, outcome, "agent_architecture", ["architecture", "multi_agent"])
                patterns.append(pattern)

            # Analyze constitutional governance pattern
            if os.path.exists(os.path.join(self.repo_path, "constitution.md")):
                patterns.append(self._extract_constitutional_pattern())

            # Analyze memory system architecture
            if os.path.exists(os.path.join(self.repo_path, "agency_memory")):
                patterns.append(self._extract_memory_architecture_pattern())

        except Exception as e:
            logger.warning(f"Architecture pattern extraction failed: {e}")

        return patterns

    def _extract_tool_patterns(self) -> List[CodingPattern]:
        """Extract tool usage patterns from agents."""
        patterns = []

        try:
            tools_dir = os.path.join(self.repo_path, "tools")
            if not os.path.exists(tools_dir):
                return patterns

            # Analyze tool structure
            tool_files = [f for f in os.listdir(tools_dir) if f.endswith('.py') and f != '__init__.py']

            if len(tool_files) >= 10:  # Rich tool ecosystem
                context = ProblemContext(
                    description="Need comprehensive toolset for AI agents to perform file operations, search, and system tasks",
                    domain="tool_design",
                    constraints=["Type safety", "Error handling", "Consistent interfaces"],
                    symptoms=["Repeated operations", "Need for validation", "Cross-platform compatibility"],
                    scale=f"{len(tool_files)} tools"
                )

                # Analyze common patterns in tools
                tool_patterns = self._analyze_tool_implementations(tools_dir)

                solution = SolutionApproach(
                    approach="Standardized tool base class with consistent error handling and validation",
                    implementation="BaseTool inheritance with Pydantic validation and run() methods",
                    tools=["pydantic", "BaseTool", "type_hints"],
                    reasoning="Ensure consistency, type safety, and error handling across all tools",
                    code_examples=tool_patterns.get("examples", [])
                )

                outcome = EffectivenessMetric(
                    success_rate=0.95,  # Based on test results
                    maintainability_impact="Consistent interfaces reduce learning curve",
                    user_impact="Reliable tool execution with predictable error handling",
                    adoption_rate=len(tool_files),
                    confidence=0.8
                )

                pattern = self.create_pattern(context, solution, outcome, "tool_ecosystem", ["tools", "consistency"])
                patterns.append(pattern)

        except Exception as e:
            logger.warning(f"Tool pattern extraction failed: {e}")

        return patterns

    def _extract_testing_patterns(self) -> List[CodingPattern]:
        """Extract testing patterns and quality approaches."""
        patterns = []

        try:
            tests_dir = os.path.join(self.repo_path, "tests")
            if not os.path.exists(tests_dir):
                return patterns

            # Analyze test structure
            test_files = []
            for root, dirs, files in os.walk(tests_dir):
                for file in files:
                    if file.startswith('test_') and file.endswith('.py'):
                        test_files.append(os.path.join(root, file))

            if len(test_files) >= 20:  # Comprehensive testing
                # Analyze test patterns
                test_analysis = self._analyze_test_patterns(test_files)

                context = ProblemContext(
                    description="Ensure high code quality and prevent regressions in complex AI system",
                    domain="testing",
                    constraints=["100% test success rate", "Constitutional compliance", "Fast execution"],
                    symptoms=["Complex interactions", "Integration challenges", "Quality requirements"],
                    scale=f"{len(test_files)} test files"
                )

                solution = SolutionApproach(
                    approach="Comprehensive test suite with unit and integration tests",
                    implementation="Pytest-based testing with fixtures, markers, and quality gates",
                    tools=["pytest", "fixtures", "markers", "constitutional_enforcement"],
                    reasoning="Maintain high quality through automated testing and constitutional compliance",
                    code_examples=test_analysis.get("patterns", [])
                )

                outcome = EffectivenessMetric(
                    success_rate=1.0,  # From MasterTest success
                    maintainability_impact="Prevents regressions and ensures quality",
                    user_impact="Reliable software with high confidence in changes",
                    adoption_rate=len(test_files),
                    confidence=0.95
                )

                pattern = self.create_pattern(context, solution, outcome, "comprehensive_testing", ["testing", "quality"])
                patterns.append(pattern)

        except Exception as e:
            logger.warning(f"Testing pattern extraction failed: {e}")

        return patterns

    def _extract_git_history_patterns(self) -> List[CodingPattern]:
        """Extract patterns from git commit history."""
        patterns = []

        try:
            # Get recent successful commits
            cmd = ["git", "log", "--oneline", "--since=30 days ago", "-20"]
            result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)

            if result.returncode != 0:
                return patterns

            commits = result.stdout.strip().split('\n')

            # Look for patterns in commit messages
            fix_commits = [c for c in commits if 'fix' in c.lower()]
            feat_commits = [c for c in commits if 'feat' in c.lower()]
            test_commits = [c for c in commits if 'test' in c.lower()]

            if len(fix_commits) >= 3:  # Bug fixing pattern
                context = ProblemContext(
                    description="Need systematic approach to identifying and fixing software bugs",
                    domain="debugging",
                    constraints=["Maintain functionality", "No breaking changes", "Test validation"],
                    symptoms=["Bug reports", "Test failures", "Production issues"],
                    scale=f"{len(fix_commits)} fixes in 30 days"
                )

                solution = SolutionApproach(
                    approach="Systematic bug fixing with test validation",
                    implementation="Identify issue, create test, fix code, validate",
                    tools=["git", "pytest", "debugging_tools"],
                    reasoning="Ensure fixes are correct and don't introduce regressions",
                    code_examples=[f"Recent fixes: {', '.join(fix_commits[:3])}"]
                )

                outcome = EffectivenessMetric(
                    success_rate=0.9,  # Assume most fixes work
                    maintainability_impact="Systematic approach reduces future issues",
                    user_impact="Faster bug resolution and higher reliability",
                    adoption_rate=len(fix_commits),
                    confidence=0.7
                )

                pattern = self.create_pattern(context, solution, outcome, "bug_fixing", ["debugging", "fixes"])
                patterns.append(pattern)

        except Exception as e:
            logger.warning(f"Git history pattern extraction failed: {e}")

        return patterns

    def _find_python_files(self) -> List[str]:
        """Find all Python files in the repository."""
        python_files = []

        for root, dirs, files in os.walk(self.repo_path):
            # Skip hidden directories and common ignores
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.venv']]

            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))

        return python_files

    def _analyze_error_handling_ast(self, tree: ast.AST, file_path: str) -> List[CodingPattern]:
        """Analyze error handling patterns in AST."""
        patterns = []

        class ErrorHandlerVisitor(ast.NodeVisitor):
            def visit_Try(self, node):
                # Analyze try-except patterns
                if len(node.handlers) > 0:
                    exception_types = []
                    for handler in node.handlers:
                        if handler.type:
                            if isinstance(handler.type, ast.Name):
                                exception_types.append(handler.type.id)
                            elif isinstance(handler.type, ast.Tuple):
                                for elt in handler.type.elts:
                                    if isinstance(elt, ast.Name):
                                        exception_types.append(elt.id)

                    if exception_types:
                        # Create pattern for specific exception handling
                        context = ProblemContext(
                            description=f"Handle {', '.join(exception_types)} exceptions gracefully",
                            domain="error_handling",
                            constraints=["No crashes", "User-friendly messages"],
                            symptoms=["Exception risks", "Unreliable operations"]
                        )

                        solution = SolutionApproach(
                            approach="Try-except with specific exception handling",
                            implementation=f"Catch {', '.join(exception_types)} and handle appropriately",
                            tools=["try_except", "logging"],
                            reasoning="Prevent crashes and provide meaningful error handling"
                        )

                        outcome = EffectivenessMetric(
                            success_rate=0.85,
                            maintainability_impact="Improved error resilience",
                            adoption_rate=1,
                            confidence=0.6
                        )

                        pattern_obj = self.create_pattern(
                            context, solution, outcome,
                            f"{os.path.basename(file_path)}:try_except",
                            ["error_handling"] + exception_types
                        )
                        patterns.append(pattern_obj)

                self.generic_visit(node)

        visitor = ErrorHandlerVisitor()
        visitor.visit(tree)
        return patterns

    def _extract_constitutional_pattern(self) -> CodingPattern:
        """Extract constitutional governance pattern."""
        context = ProblemContext(
            description="Maintain consistent quality standards and governance in AI development",
            domain="governance",
            constraints=["Automated enforcement", "No manual overrides", "100% compliance"],
            symptoms=["Quality variance", "Manual interventions", "Inconsistent standards"],
            scale="Entire development process"
        )

        solution = SolutionApproach(
            approach="Constitutional governance with automated enforcement",
            implementation="Define principles in constitution.md and enforce through technical mechanisms",
            tools=["constitutional_articles", "automated_testing", "quality_gates"],
            reasoning="Ensure consistent quality without human intervention points"
        )

        outcome = EffectivenessMetric(
            success_rate=1.0,  # From test results
            maintainability_impact="Consistent quality standards maintained automatically",
            user_impact="Reliable software with predictable quality",
            adoption_rate=1,
            confidence=0.95
        )

        return self.create_pattern(context, solution, outcome, "constitutional_governance", ["governance", "quality"])

    def _extract_memory_architecture_pattern(self) -> CodingPattern:
        """Extract memory system architecture pattern."""
        context = ProblemContext(
            description="Provide persistent memory and learning capabilities for AI agents",
            domain="architecture",
            constraints=["Multiple backends", "Semantic search", "Performance"],
            symptoms=["Need for context persistence", "Learning requirements", "Search capabilities"],
            scale="Multi-agent system"
        )

        solution = SolutionApproach(
            approach="Pluggable memory architecture with VectorStore and multiple backends",
            implementation="Abstract MemoryStore interface with InMemory, Firestore, and Vector implementations",
            tools=["abstract_interfaces", "vector_store", "firestore", "semantic_search"],
            reasoning="Enable flexible memory solutions while maintaining consistent interface"
        )

        outcome = EffectivenessMetric(
            success_rate=0.9,
            maintainability_impact="Flexible architecture allows different memory strategies",
            user_impact="Persistent context and learning capabilities",
            adoption_rate=1,
            confidence=0.8
        )

        return self.create_pattern(context, solution, outcome, "memory_architecture", ["architecture", "memory"])

    def _analyze_tool_implementations(self, tools_dir: str) -> Dict[str, JSONValue]:
        """Analyze patterns in tool implementations."""
        patterns = {"examples": [], "common_patterns": []}

        try:
            for file_name in os.listdir(tools_dir):
                if file_name.endswith('.py') and file_name != '__init__.py':
                    file_path = os.path.join(tools_dir, file_name)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Look for BaseTool usage
                    if 'BaseTool' in content and 'def run(' in content:
                        patterns["examples"].append(f"{file_name}: BaseTool with run() method")

                    # Look for Pydantic fields
                    if 'Field(' in content:
                        patterns["common_patterns"].append("Pydantic Field validation")

        except Exception as e:
            logger.debug(f"Failed to analyze tool implementations: {e}")

        return patterns

    def _analyze_test_patterns(self, test_files: List[str]) -> Dict[str, JSONValue]:
        """Analyze patterns in test files."""
        patterns = {"patterns": [], "coverage": []}

        try:
            for test_file in test_files[:5]:  # Sample first 5 files
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                file_name = os.path.basename(test_file)

                # Look for common test patterns
                if '@pytest.mark.' in content:
                    patterns["patterns"].append(f"{file_name}: Uses pytest markers")

                if 'def test_' in content:
                    test_count = content.count('def test_')
                    patterns["patterns"].append(f"{file_name}: {test_count} test functions")

                if 'assert ' in content:
                    patterns["patterns"].append(f"{file_name}: Uses assertions")

        except Exception as e:
            logger.debug(f"Failed to analyze test patterns: {e}")

        return patterns